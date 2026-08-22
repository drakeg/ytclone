from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Channel, ChannelMembership, ChannelTeamInvitation, Notification


class ChannelTeamNotificationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.invitee = User.objects.create_user(username="invitee", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.channel = Channel.objects.create(owner=self.owner, name="Team channel", description="Team")
        self.team_url = reverse("channel_team", args=[self.channel.pk])

    def invite(self):
        self.client.force_login(self.owner)
        self.client.post(self.team_url, {"username": self.invitee.username})
        return ChannelTeamInvitation.objects.get(invitee=self.invitee)

    def test_invite_creates_one_private_notification_linked_to_inbox(self):
        self.invite()
        notification = Notification.objects.get()
        self.assertEqual(notification.recipient, self.invitee)
        self.assertEqual(notification.kind, Notification.Kind.TEAM_INVITATION)

        self.client.force_login(self.invitee)
        response = self.client.get(reverse("notification_list"))
        self.assertContains(response, "invited you to edit")
        self.assertContains(response, reverse("channel_team_invitations"))
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse("notification_list")), self.channel.name)

    def test_navigation_counts_only_unexpired_pending_invitations(self):
        invitation = self.invite()
        self.client.force_login(self.invitee)
        response = self.client.get(reverse("video_list"))
        self.assertEqual(response.context["pending_team_invitation_count"], 1)
        self.assertContains(response, "Team invites (1)")

        invitation.expires_at = timezone.now() - timedelta(seconds=1)
        invitation.save(update_fields=["expires_at"])
        response = self.client.get(reverse("video_list"))
        self.assertEqual(response.context["pending_team_invitation_count"], 0)

    def test_accept_and_decline_clear_unread_invitation_notification(self):
        for decision in ("accept", "decline"):
            with self.subTest(decision=decision):
                ChannelTeamInvitation.objects.all().delete()
                ChannelMembership.objects.all().delete()
                Notification.objects.all().delete()
                invitation = self.invite()
                self.client.force_login(self.invitee)
                self.client.post(reverse("channel_team_invitation_respond", args=[invitation.token, decision]))
                self.assertIsNotNone(Notification.objects.get().read_at)

    def test_owner_revoke_clears_notification_and_records_activity(self):
        invitation = self.invite()
        url = reverse("channel_team_invitation_revoke", args=[self.channel.pk, invitation.pk])
        self.client.post(url)
        self.assertIsNotNone(Notification.objects.get().read_at)
        response = self.client.get(self.team_url)
        self.assertContains(response, "Recent invitation activity")
        self.assertContains(response, "Revoked")

    def test_expired_invitation_moves_from_pending_to_activity(self):
        invitation = self.invite()
        invitation.expires_at = timezone.now() - timedelta(seconds=1)
        invitation.save(update_fields=["expires_at"])
        response = self.client.get(self.team_url)
        self.assertNotContains(response, "expires " + invitation.expires_at.strftime("%b"))
        self.assertContains(response, "Expired")

    def test_activity_history_is_owner_only_and_bounded(self):
        for index in range(30):
            user = User.objects.create_user(username=f"past-{index}")
            ChannelTeamInvitation.objects.create(channel=self.channel, invitee=user, invited_by=self.owner, status=ChannelTeamInvitation.Status.DECLINED, expires_at=timezone.now(), responded_at=timezone.now())
        self.client.force_login(self.owner)
        response = self.client.get(self.team_url)
        self.assertEqual(len(response.context["invitation_activity"]), 25)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.team_url).status_code, 404)
