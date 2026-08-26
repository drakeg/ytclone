from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from monetization.models import (
    ChannelMembershipSubscription,
    CreatorMonetizationAccount,
    MembershipTier,
)
from video.models import Channel, ChannelMembership, Comment, Video


class AdministrationTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff", password="password123", is_staff=True
        )
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.editor = User.objects.create_user(username="editor", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.outsider = User.objects.create_user(username="outsider", password="password123")

        self.channel = Channel.objects.create(
            owner=self.owner, name="Owned Channel", description="Creator channel"
        )
        self.other_channel = Channel.objects.create(
            owner=self.outsider, name="Other Channel", description="Other channel"
        )
        ChannelMembership.objects.create(
            channel=self.channel,
            user=self.editor,
            role=ChannelMembership.Role.EDITOR,
        )

        self.video = Video.objects.create(
            title="Editor upload",
            description="A channel video",
            thumbnail="videos/thumbnails/editor.jpg",
            video_file="videos/files/editor.mp4",
            author=self.editor,
            channel=self.channel,
        )
        self.other_video = Video.objects.create(
            title="Other upload",
            description="Unrelated",
            thumbnail="videos/thumbnails/other.jpg",
            video_file="videos/files/other.mp4",
            author=self.outsider,
            channel=self.other_channel,
        )
        self.comment = Comment.objects.create(
            video=self.video, author=self.viewer, comment="Please moderate me"
        )
        self.other_comment = Comment.objects.create(
            video=self.other_video, author=self.viewer, comment="Not your channel"
        )

    def test_site_admin_dashboard_is_staff_only(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("site_admin_dashboard"))
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.staff)
        response = self.client.get(reverse("site_admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Site Administration")
        self.assertContains(response, "Please moderate me")
        self.assertContains(response, "Not your channel")

    def test_staff_can_moderate_any_comment(self):
        self.client.force_login(self.staff)
        url = reverse("site_admin_comment_moderate", args=[self.other_comment.pk])
        response = self.client.post(url, {"action": "hide", "reason": "Abusive comment"})
        self.assertRedirects(response, reverse("site_admin_dashboard"))
        self.other_comment.refresh_from_db()
        self.assertTrue(self.other_comment.is_hidden)

        self.client.post(url, {"action": "restore", "reason": "Reviewed"})
        self.other_comment.refresh_from_db()
        self.assertFalse(self.other_comment.is_hidden)

    def test_nonstaff_cannot_use_site_moderation_endpoint(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("site_admin_comment_moderate", args=[self.comment.pk]),
            {"action": "hide", "reason": "No access"},
        )
        self.assertEqual(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertFalse(self.comment.is_hidden)

    def test_creator_owner_can_moderate_editor_uploaded_video_comments(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("creator_comment_list"))
        self.assertContains(response, "Please moderate me")
        self.assertNotContains(response, "Not your channel")

        response = self.client.post(
            reverse("creator_comment_bulk_moderation"),
            {"comment_ids": [self.comment.pk, self.other_comment.pk], "action": "hide"},
        )
        self.assertRedirects(response, reverse("creator_comment_list"))
        self.comment.refresh_from_db()
        self.other_comment.refresh_from_db()
        self.assertTrue(self.comment.is_hidden)
        self.assertFalse(self.other_comment.is_hidden)

    def test_channel_editor_can_moderate_comments_in_assigned_channel_only(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse("creator_comment_list"))
        self.assertContains(response, "Please moderate me")
        self.assertNotContains(response, "Not your channel")

    def test_owner_audience_page_shows_free_and_paid_memberships(self):
        self.channel.subscribers.add(self.viewer)
        account = CreatorMonetizationAccount.objects.create(channel=self.channel)
        tier = MembershipTier.objects.create(
            monetization_account=account,
            name="Supporter",
            description="Supporter tier",
            price_minor=500,
        )
        ChannelMembershipSubscription.objects.create(
            tier=tier,
            subscriber=self.viewer,
            status=ChannelMembershipSubscription.Status.ACTIVE,
        )

        self.client.force_login(self.owner)
        response = self.client.get(reverse("creator_audience"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Audience")
        self.assertContains(response, self.viewer.username)
        self.assertContains(response, "Supporter")
        self.assertContains(response, "Active")

    def test_editor_cannot_view_owner_paid_audience(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse("creator_audience"))
        self.assertEqual(response.status_code, 404)
