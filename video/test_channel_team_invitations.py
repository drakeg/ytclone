from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from .forms import VideoUploadForm
from .models import Channel, ChannelMembership, ChannelTeamInvitation


class ChannelTeamInvitationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.invitee = User.objects.create_user(username="invitee", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.channel = Channel.objects.create(
            owner=self.owner,
            name="Invitation Channel",
            description="Team invitations",
        )
        self.team_url = reverse("channel_team", args=[self.channel.pk])

    def invite(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.team_url, {"username": self.invitee.username})
        self.assertRedirects(response, self.team_url)
        return ChannelTeamInvitation.objects.get(
            invitee=self.invitee,
            status=ChannelTeamInvitation.Status.PENDING,
        )

    def respond_url(self, invitation, decision):
        return reverse(
            "channel_team_invitation_respond",
            args=[invitation.token, decision],
        )

    def test_invitation_is_pending_for_seven_days_and_grants_no_access(self):
        before = timezone.now()
        invitation = self.invite()

        self.assertEqual(invitation.status, ChannelTeamInvitation.Status.PENDING)
        self.assertGreaterEqual(invitation.expires_at, before + timedelta(days=7))
        self.assertFalse(ChannelMembership.objects.exists())
        form = VideoUploadForm(user=self.invitee)
        self.assertNotIn(self.channel, form.fields["channel"].queryset)

    def test_only_recipient_sees_invitation_and_can_accept_it_with_post(self):
        invitation = self.invite()
        inbox = reverse("channel_team_invitations")

        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(inbox), self.channel.name)
        self.assertEqual(self.client.post(self.respond_url(invitation, "accept")).status_code, 404)

        self.client.force_login(self.invitee)
        self.assertContains(self.client.get(inbox), self.channel.name)
        self.assertEqual(self.client.get(self.respond_url(invitation, "accept")).status_code, 405)
        response = self.client.post(self.respond_url(invitation, "accept"))

        self.assertRedirects(response, inbox)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelTeamInvitation.Status.ACCEPTED)
        self.assertIsNotNone(invitation.responded_at)
        self.assertTrue(
            ChannelMembership.objects.filter(
                channel=self.channel,
                user=self.invitee,
            ).exists()
        )
        self.assertIn(self.channel, VideoUploadForm(user=self.invitee).fields["channel"].queryset)
        self.assertEqual(self.client.post(self.respond_url(invitation, "accept")).status_code, 404)

    def test_recipient_can_decline_without_becoming_editor(self):
        invitation = self.invite()
        self.client.force_login(self.invitee)

        response = self.client.post(self.respond_url(invitation, "decline"))

        self.assertRedirects(response, reverse("channel_team_invitations"))
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelTeamInvitation.Status.DECLINED)
        self.assertFalse(ChannelMembership.objects.exists())

    def test_expired_invitation_cannot_be_accepted(self):
        invitation = self.invite()
        invitation.expires_at = timezone.now() - timedelta(seconds=1)
        invitation.save(update_fields=["expires_at"])
        self.client.force_login(self.invitee)

        self.assertEqual(self.client.post(self.respond_url(invitation, "accept")).status_code, 404)

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelTeamInvitation.Status.EXPIRED)
        self.assertFalse(ChannelMembership.objects.exists())

    def test_owner_can_revoke_pending_invitation_with_post_only(self):
        invitation = self.invite()
        url = reverse(
            "channel_team_invitation_revoke",
            args=[self.channel.pk, invitation.pk],
        )

        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), self.team_url)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelTeamInvitation.Status.REVOKED)

    def test_other_channel_owner_cannot_revoke_invitation(self):
        invitation = self.invite()
        self.client.force_login(self.other)
        url = reverse(
            "channel_team_invitation_revoke",
            args=[self.channel.pk, invitation.pk],
        )

        self.assertEqual(self.client.post(url).status_code, 404)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelTeamInvitation.Status.PENDING)

    def test_expired_pending_invitation_is_replaced_by_new_invitation(self):
        invitation = self.invite()
        invitation.expires_at = timezone.now() - timedelta(seconds=1)
        invitation.save(update_fields=["expires_at"])

        replacement = self.invite()

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelTeamInvitation.Status.EXPIRED)
        self.assertNotEqual(replacement.pk, invitation.pk)
        self.assertEqual(replacement.status, ChannelTeamInvitation.Status.PENDING)

    def test_invalid_response_decision_is_rejected(self):
        invitation = self.invite()
        self.client.force_login(self.invitee)

        self.assertEqual(self.client.post(self.respond_url(invitation, "approve")).status_code, 404)
        self.assertFalse(ChannelMembership.objects.exists())


    @override_settings(
        TEAM_INVITATION_EMAIL_ENABLED=False,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_invitation_email_is_disabled_by_default_behavior(self):
        self.invitee.email = "invitee@example.com"
        self.invitee.save(update_fields=["email"])

        self.invite()

        self.assertEqual(len(mail.outbox), 0)

    @override_settings(
        TEAM_INVITATION_EMAIL_ENABLED=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="videoshare@example.com",
    )
    def test_enabled_invitation_email_contains_channel_inviter_expiration_and_inbox_link(self):
        self.invitee.email = "invitee@example.com"
        self.invitee.save(update_fields=["email"])

        invitation = self.invite()

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["invitee@example.com"])
        self.assertEqual(email.from_email, "videoshare@example.com")
        self.assertIn(self.channel.name, email.subject)
        self.assertIn(self.owner.username, email.body)
        self.assertIn(self.channel.name, email.body)
        self.assertIn(
            reverse("channel_team_invitations"),
            email.body,
        )
        self.assertNotIn(str(invitation.token), email.body)

    @override_settings(
        TEAM_INVITATION_EMAIL_ENABLED=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_invitee_without_email_keeps_in_app_invitation_without_email(self):
        invitation = self.invite()

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(invitation.status, ChannelTeamInvitation.Status.PENDING)

    @override_settings(TEAM_INVITATION_EMAIL_ENABLED=True)
    @patch("video.services.team_invitations.send_mail", side_effect=RuntimeError("mail unavailable"))
    def test_email_failure_does_not_rollback_invitation(self, mocked_send_mail):
        self.invitee.email = "invitee@example.com"
        self.invitee.save(update_fields=["email"])

        invitation = self.invite()

        mocked_send_mail.assert_called_once()
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ChannelTeamInvitation.Status.PENDING)
        self.assertTrue(
            self.invitee.notifications.filter(
                kind="team_invite",
                channel=self.channel,
            ).exists()
        )

    @override_settings(
        TEAM_INVITATION_EMAIL_ENABLED=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_duplicate_pending_invitation_does_not_emit_second_email(self):
        self.invitee.email = "invitee@example.com"
        self.invitee.save(update_fields=["email"])
        self.invite()
        self.assertEqual(len(mail.outbox), 1)

        response = self.client.post(
            self.team_url,
            {"username": self.invitee.username},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already has a pending invitation")
        self.assertEqual(len(mail.outbox), 1)
