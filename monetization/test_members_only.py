from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from video.models import Channel, Video

from .models import (
    ChannelMembershipSubscription,
    CreatorMonetizationAccount,
    MembershipTier,
    MonetizationTransaction,
)


@override_settings(MONETIZATION_PLATFORM_FEE_BPS=1000)
class MonetizationExperienceTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.free_subscriber = User.objects.create_user(
            username="freeviewer", password="password123"
        )
        self.channel = Channel.objects.create(
            owner=self.creator,
            name="Creator Channel",
            description="Creator content",
        )

    def _enable_account(self):
        return CreatorMonetizationAccount.objects.create(
            channel=self.channel,
            status=CreatorMonetizationAccount.Status.ACTIVE,
            terms_accepted_at=timezone.now(),
            payouts_enabled=True,
            provider="test",
            provider_account_id="acct_test_creator",
        )

    def _tier(self):
        account = self._enable_account()
        return MembershipTier.objects.create(
            monetization_account=account,
            name="Supporter",
            description="Bonus videos",
            price_minor=500,
            currency="USD",
        )

    def _members_video(self):
        return Video.objects.create(
            title="Members bonus",
            description="Extra video for members",
            thumbnail="videos/thumbnails/bonus.jpg",
            video_file="videos/files/bonus.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
            audience=Video.Audience.MEMBERS_ONLY,
        )

    def test_creator_can_enable_sandbox_monetization_without_thresholds(self):
        self.client.login(username="creator", password="password123")
        response = self.client.post(
            reverse("monetization:enable_sandbox", kwargs={"pk": self.channel.pk})
        )

        self.assertRedirects(
            response,
            reverse("monetization:creator_dashboard", kwargs={"pk": self.channel.pk}),
        )
        account = CreatorMonetizationAccount.objects.get(channel=self.channel)
        self.assertTrue(account.is_ready_to_earn)
        self.assertEqual(self.channel.subscribers.count(), 0)
        self.assertEqual(self.channel.videos.count(), 0)

    def test_creator_can_create_membership_tier(self):
        self._enable_account()
        self.client.login(username="creator", password="password123")

        response = self.client.post(
            reverse("monetization:tier_create", kwargs={"pk": self.channel.pk}),
            {
                "name": "Supporter",
                "description": "Bonus videos",
                "monthly_price": "5.00",
            },
        )

        self.assertRedirects(
            response,
            reverse("monetization:creator_dashboard", kwargs={"pk": self.channel.pk}),
        )
        tier = MembershipTier.objects.get(name="Supporter")
        self.assertEqual(tier.price_minor, 500)

    def test_sandbox_membership_records_creator_and_platform_share(self):
        tier = self._tier()
        self.client.login(username="viewer", password="password123")

        response = self.client.post(
            reverse("monetization:join_sandbox_membership", kwargs={"tier_pk": tier.pk})
        )

        self.assertRedirects(
            response, reverse("channel_detail", kwargs={"pk": self.channel.pk})
        )
        membership = ChannelMembershipSubscription.objects.get(
            subscriber=self.viewer, tier=tier
        )
        self.assertEqual(membership.status, ChannelMembershipSubscription.Status.ACTIVE)
        transaction = MonetizationTransaction.objects.get(
            membership_subscription=membership
        )
        self.assertEqual(transaction.gross_amount_minor, 500)
        self.assertEqual(transaction.platform_fee_minor, 50)
        self.assertEqual(transaction.creator_net_minor, 450)

    def test_channel_owner_cannot_join_own_paid_membership(self):
        tier = self._tier()
        self.client.login(username="creator", password="password123")

        response = self.client.post(
            reverse("monetization:join_sandbox_membership", kwargs={"tier_pk": tier.pk})
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(ChannelMembershipSubscription.objects.exists())

    def test_members_only_video_is_hidden_from_anonymous_and_nonmember(self):
        video = self._members_video()

        self.assertFalse(Video.objects.visible_to(AnonymousUser()).filter(pk=video.pk).exists())
        self.assertFalse(Video.objects.visible_to(self.viewer).filter(pk=video.pk).exists())

    def test_free_channel_subscription_does_not_unlock_members_only_video(self):
        video = self._members_video()
        self.channel.subscribers.add(self.free_subscriber)

        self.assertFalse(
            Video.objects.visible_to(self.free_subscriber).filter(pk=video.pk).exists()
        )

    def test_active_paid_member_can_see_members_only_video(self):
        tier = self._tier()
        video = self._members_video()
        ChannelMembershipSubscription.objects.create(
            subscriber=self.viewer,
            tier=tier,
            status=ChannelMembershipSubscription.Status.ACTIVE,
        )

        self.assertTrue(Video.objects.visible_to(self.viewer).filter(pk=video.pk).exists())
        self.client.login(username="viewer", password="password123")
        response = self.client.get(reverse("video_detail", kwargs={"pk": video.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Members bonus")

    def test_creator_can_always_view_own_members_only_video(self):
        video = self._members_video()

        self.assertTrue(Video.objects.visible_to(self.creator).filter(pk=video.pk).exists())
