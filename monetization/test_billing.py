from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from video.models import Channel
from .models import ChannelMembershipSubscription, CreatorMonetizationAccount, MembershipTier


class MembershipBillingTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="billingcreator", password="password123")
        self.viewer = User.objects.create_user(username="billingviewer", password="password123")
        self.other = User.objects.create_user(username="billingother", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Billing Channel")
        self.account = CreatorMonetizationAccount.objects.create(channel=self.channel)
        self.tier = MembershipTier.objects.create(monetization_account=self.account, name="Supporter", price_minor=700)

    def test_billing_page_requires_login(self):
        response = self.client.get(reverse("monetization:membership_billing"))
        self.assertEqual(response.status_code, 302)

    def test_billing_page_only_lists_current_users_memberships(self):
        mine = ChannelMembershipSubscription.objects.create(tier=self.tier, subscriber=self.viewer, provider_subscription_id="sub_test_viewer")
        ChannelMembershipSubscription.objects.create(tier=self.tier, subscriber=self.other, provider_subscription_id="sub_test_other")
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("monetization:membership_billing"))
        self.assertContains(response, "Billing Channel")
        self.assertContains(response, "Supporter")
        self.assertContains(response, reverse("monetization:cancel_stripe_membership", args=[mine.pk]))
        self.assertNotContains(response, "billingother")

    def test_sandbox_membership_uses_sandbox_cancel_action(self):
        membership = ChannelMembershipSubscription.objects.create(tier=self.tier, subscriber=self.viewer, provider_subscription_id="test_sub_123")
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("monetization:membership_billing"))
        self.assertContains(response, reverse("monetization:cancel_sandbox_membership", args=[membership.pk]))
