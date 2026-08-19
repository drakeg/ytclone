from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from video.models import Channel
from .models import ChannelMembershipSubscription, CreatorMonetizationAccount, MembershipTier


class MembershipLifecycleTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creatorlife", password="password123")
        self.viewer = User.objects.create_user(username="viewerlif", password="password123")
        self.other = User.objects.create_user(username="otherlife", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Lifecycle Channel")
        self.account = CreatorMonetizationAccount.objects.create(channel=self.channel, status=CreatorMonetizationAccount.Status.ACTIVE, terms_accepted_at=timezone.now(), payouts_enabled=True, provider="test")
        self.basic = MembershipTier.objects.create(monetization_account=self.account, name="Basic", price_minor=500)
        self.plus = MembershipTier.objects.create(monetization_account=self.account, name="Plus", price_minor=1000)

    def test_creator_can_edit_owned_tier(self):
        self.client.force_login(self.creator)
        response = self.client.post(reverse("monetization:tier_edit", args=[self.basic.pk]), {"name": "Supporter", "description": "Updated", "monthly_price": "6.00"})
        self.assertRedirects(response, reverse("monetization:creator_dashboard", args=[self.channel.pk]))
        self.basic.refresh_from_db()
        self.assertEqual(self.basic.name, "Supporter")
        self.assertEqual(self.basic.price_minor, 600)

    def test_non_owner_cannot_edit_tier(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("monetization:tier_edit", args=[self.basic.pk]))
        self.assertEqual(response.status_code, 404)

    def test_creator_can_stop_new_joins_without_canceling_existing_members(self):
        subscription = ChannelMembershipSubscription.objects.create(tier=self.basic, subscriber=self.viewer)
        self.client.force_login(self.creator)
        self.client.post(reverse("monetization:tier_toggle", args=[self.basic.pk]))
        self.basic.refresh_from_db(); subscription.refresh_from_db()
        self.assertFalse(self.basic.is_active)
        self.assertEqual(subscription.status, ChannelMembershipSubscription.Status.ACTIVE)

    def test_member_can_cancel_own_membership(self):
        subscription = ChannelMembershipSubscription.objects.create(tier=self.basic, subscriber=self.viewer)
        self.client.force_login(self.viewer)
        response = self.client.post(reverse("monetization:cancel_sandbox_membership", args=[subscription.pk]))
        self.assertRedirects(response, reverse("channel_detail", args=[self.channel.pk]))
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, ChannelMembershipSubscription.Status.CANCELED)
        self.assertIsNotNone(subscription.canceled_at)
        self.assertIsNotNone(subscription.ended_at)

    def test_user_cannot_cancel_another_users_membership(self):
        subscription = ChannelMembershipSubscription.objects.create(tier=self.basic, subscriber=self.viewer)
        self.client.force_login(self.other)
        response = self.client.post(reverse("monetization:cancel_sandbox_membership", args=[subscription.pk]))
        self.assertEqual(response.status_code, 404)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, ChannelMembershipSubscription.Status.ACTIVE)

    def test_switching_tiers_ends_old_membership_and_activates_new_one(self):
        old = ChannelMembershipSubscription.objects.create(tier=self.basic, subscriber=self.viewer)
        self.client.force_login(self.viewer)
        self.client.post(reverse("monetization:join_sandbox_membership", args=[self.plus.pk]))
        old.refresh_from_db()
        new = ChannelMembershipSubscription.objects.get(tier=self.plus, subscriber=self.viewer)
        self.assertEqual(old.status, ChannelMembershipSubscription.Status.ENDED)
        self.assertEqual(new.status, ChannelMembershipSubscription.Status.ACTIVE)
