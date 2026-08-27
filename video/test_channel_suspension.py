from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.urls import reverse

from monetization.models import ChannelMembershipSubscription, CreatorMonetizationAccount, MembershipTier

from .models import Channel, Video
from .moderation_models import ChannelModerationState, ModerationAuditEvent
from .services.search import search_content


class ChannelSuspensionTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="staff", password="password123", is_staff=True)
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Suspension Test Channel", description="Distinct channel description")
        self.video = Video.objects.create(title="Suspension Test Video", description="", thumbnail="videos/thumbnails/a.jpg", video_file="videos/files/a.mp4", author=self.creator, channel=self.channel, publication_status=Video.PublicationStatus.PUBLISHED)

    def suspend(self):
        self.client.force_login(self.staff)
        return self.client.post(reverse("site_admin_channel_moderate", args=[self.channel.pk]), {"action": "suspend", "reason": "Policy review"})

    def test_staff_suspension_requires_reason_and_is_audited(self):
        self.client.force_login(self.staff)
        url = reverse("site_admin_channel_moderate", args=[self.channel.pk])
        self.assertEqual(self.client.post(url, {"action": "suspend", "reason": ""}).status_code, 400)
        self.client.post(url, {"action": "suspend", "reason": "Policy review"})
        self.assertTrue(ChannelModerationState.objects.filter(channel=self.channel).exists())
        self.assertTrue(ModerationAuditEvent.objects.filter(action="channel_suspend", target_type="channel", target_id=self.channel.pk).exists())

    def test_suspended_channel_disappears_from_video_visibility_directory_search_and_direct_pages(self):
        self.suspend()
        self.assertFalse(Video.objects.visible_to(AnonymousUser()).filter(pk=self.video.pk).exists())
        self.client.logout()
        self.assertNotContains(self.client.get(reverse("channel_list")), "Suspension Test Channel")
        self.assertEqual(self.client.get(reverse("channel_detail", args=[self.channel.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("channel_community", args=[self.channel.pk])).status_code, 404)
        results = search_content("Suspension Test", "relevance", AnonymousUser())
        self.assertFalse(results.channels.filter(pk=self.channel.pk).exists())
        self.assertFalse(results.videos.filter(pk=self.video.pk).exists())

    def test_owner_cannot_view_suspended_channel_video_but_staff_can_inspect(self):
        self.suspend()
        self.assertFalse(Video.objects.visible_to(self.creator).filter(pk=self.video.pk).exists())
        self.assertTrue(Video.objects.visible_to(self.staff).filter(pk=self.video.pk).exists())
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("channel_detail", args=[self.channel.pk])).status_code, 200)

    def test_paid_membership_does_not_bypass_channel_suspension(self):
        account = CreatorMonetizationAccount.objects.create(channel=self.channel)
        tier = MembershipTier.objects.create(monetization_account=account, name="Supporter", price_cents=500)
        ChannelMembershipSubscription.objects.create(tier=tier, subscriber=self.viewer, status=ChannelMembershipSubscription.Status.ACTIVE)
        self.video.audience = Video.Audience.MEMBERS_ONLY
        self.video.save(update_fields=["audience"])
        self.assertTrue(Video.objects.visible_to(self.viewer).filter(pk=self.video.pk).exists())
        self.suspend()
        self.assertFalse(Video.objects.visible_to(self.viewer).filter(pk=self.video.pk).exists())
        self.assertFalse(self.video.has_member_access(self.viewer))

    def test_restore_preserves_data_and_returns_content_to_visibility(self):
        self.channel.subscribers.add(self.viewer)
        self.suspend()
        self.client.post(reverse("site_admin_channel_moderate", args=[self.channel.pk]), {"action": "restore", "reason": "Review complete"})
        self.assertFalse(ChannelModerationState.objects.filter(channel=self.channel).exists())
        self.assertTrue(ModerationAuditEvent.objects.filter(action="channel_restore", target_id=self.channel.pk).exists())
        self.assertTrue(Channel.objects.filter(pk=self.channel.pk, subscribers=self.viewer).exists())
        self.assertTrue(Video.objects.visible_to(AnonymousUser()).filter(pk=self.video.pk).exists())
