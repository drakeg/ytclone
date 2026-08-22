from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from video.models import Channel
from .models import ChannelMembershipSubscription, CreatorMonetizationAccount, MembershipTier, MonetizationTransaction


@override_settings(
    MONETIZATION_PAYMENT_PROVIDER="stripe",
    STRIPE_SECRET_KEY="sk_test_example",
    STRIPE_WEBHOOK_SECRET="whsec_example",
    MONETIZATION_PLATFORM_FEE_BPS=1000,
)
class StripeTestModeViewsTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="stripecreator", password="password123", email="creator@example.com")
        self.viewer = User.objects.create_user(username="stripeviewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Stripe Channel")
        self.account = CreatorMonetizationAccount.objects.create(
            channel=self.channel,
            status=CreatorMonetizationAccount.Status.ACTIVE,
            terms_accepted_at=timezone.now(),
            payouts_enabled=True,
            provider="stripe",
            provider_account_id="acct_test_creator",
        )
        self.tier = MembershipTier.objects.create(
            monetization_account=self.account,
            name="Supporter",
            price_minor=500,
            currency="USD",
        )

    @patch("monetization.views.stripe_gateway.create_tip_checkout")
    def test_tip_starts_stripe_checkout(self, create_checkout):
        create_checkout.return_value = SimpleNamespace(url="https://checkout.stripe.test/session", session_id="cs_test_1")
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("monetization:start_stripe_tip", args=[self.channel.pk]),
            {"amount": "10.00"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://checkout.stripe.test/session")
        kwargs = create_checkout.call_args.kwargs
        self.assertEqual(kwargs["amount_minor"], 1000)
        self.assertEqual(kwargs["connected_account_id"], "acct_test_creator")

    @patch("monetization.views.stripe_gateway.create_membership_checkout")
    def test_membership_starts_stripe_subscription_checkout(self, create_checkout):
        create_checkout.return_value = SimpleNamespace(url="https://checkout.stripe.test/member", session_id="cs_test_2")
        self.client.force_login(self.viewer)

        response = self.client.post(reverse("monetization:start_stripe_membership", args=[self.tier.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://checkout.stripe.test/member")
        self.assertEqual(create_checkout.call_args.kwargs["price_minor"], 500)

    @patch("monetization.views.stripe_gateway.create_membership_checkout")
    def test_existing_membership_prevents_second_stripe_checkout(self, create_checkout):
        second_tier = MembershipTier.objects.create(
            monetization_account=self.account,
            name="Sponsor",
            price_minor=1000,
            currency="USD",
        )
        ChannelMembershipSubscription.objects.create(
            tier=self.tier,
            subscriber=self.viewer,
            provider_subscription_id="sub_existing",
        )
        self.client.force_login(self.viewer)

        same_tier = self.client.post(
            reverse("monetization:start_stripe_membership", args=[self.tier.pk])
        )
        other_tier = self.client.post(
            reverse("monetization:start_stripe_membership", args=[second_tier.pk])
        )

        self.assertRedirects(same_tier, reverse("channel_detail", args=[self.channel.pk]))
        self.assertEqual(other_tier.status_code, 400)
        create_checkout.assert_not_called()

    @patch("monetization.views.stripe_gateway.construct_webhook_event")
    def test_checkout_webhook_does_not_create_parallel_active_membership(self, construct_event):
        existing = ChannelMembershipSubscription.objects.create(
            tier=self.tier,
            subscriber=self.viewer,
            provider_subscription_id="sub_existing",
        )
        second_tier = MembershipTier.objects.create(
            monetization_account=self.account,
            name="Sponsor",
            price_minor=1000,
            currency="USD",
        )
        construct_event.return_value = {
            "id": "evt_parallel_checkout",
            "type": "checkout.session.completed",
            "data": {"object": {
                "subscription": "sub_parallel",
                "metadata": {
                    "ytclone_kind": "membership",
                    "ytclone_tier_id": str(second_tier.pk),
                    "ytclone_payer_id": str(self.viewer.pk),
                },
            }},
        }

        response = self.client.post(
            reverse("monetization:stripe_webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            ChannelMembershipSubscription.objects.filter(
                subscriber=self.viewer,
                status=ChannelMembershipSubscription.Status.ACTIVE,
            ).count(),
            1,
        )
        self.assertEqual(existing.provider_subscription_id, "sub_existing")
        self.assertFalse(
            MonetizationTransaction.objects.filter(provider_event_id="evt_parallel_checkout").exists()
        )

    @patch("monetization.views.stripe_gateway.cancel_membership_at_period_end")
    def test_stripe_cancellation_keeps_access_until_webhook_ends_subscription(self, cancel_remote):
        subscription = ChannelMembershipSubscription.objects.create(
            tier=self.tier,
            subscriber=self.viewer,
            provider_subscription_id="sub_test_123",
        )
        self.client.force_login(self.viewer)

        response = self.client.post(reverse("monetization:cancel_stripe_membership", args=[subscription.pk]))

        self.assertRedirects(response, reverse("channel_detail", args=[self.channel.pk]))
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, ChannelMembershipSubscription.Status.ACTIVE)
        self.assertIsNotNone(subscription.canceled_at)
        self.assertIsNone(subscription.ended_at)
        cancel_remote.assert_called_once_with("sub_test_123")

    @patch("monetization.views.stripe_gateway.construct_webhook_event")
    def test_completed_tip_webhook_records_platform_split_once(self, construct_event):
        event = {
            "id": "evt_tip_1",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "currency": "usd",
                    "payment_intent": "pi_test_1",
                    "metadata": {
                        "ytclone_kind": "tip",
                        "ytclone_channel_id": str(self.channel.pk),
                        "ytclone_payer_id": str(self.viewer.pk),
                        "ytclone_gross_minor": "1000",
                        "ytclone_platform_fee_minor": "100",
                    },
                }
            },
        }
        construct_event.return_value = event
        url = reverse("monetization:stripe_webhook")

        first = self.client.post(url, data=b"{}", content_type="application/json", HTTP_STRIPE_SIGNATURE="test")
        second = self.client.post(url, data=b"{}", content_type="application/json", HTTP_STRIPE_SIGNATURE="test")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        transaction = MonetizationTransaction.objects.get(provider_event_id="evt_tip_1")
        self.assertEqual(transaction.gross_amount_minor, 1000)
        self.assertEqual(transaction.platform_fee_minor, 100)
        self.assertEqual(transaction.creator_net_minor, 900)
        self.assertEqual(MonetizationTransaction.objects.filter(provider_event_id="evt_tip_1").count(), 1)

    @patch("monetization.views.stripe_gateway.construct_webhook_event")
    def test_subscription_deleted_webhook_removes_member_access(self, construct_event):
        subscription = ChannelMembershipSubscription.objects.create(
            tier=self.tier,
            subscriber=self.viewer,
            provider_subscription_id="sub_test_delete",
        )
        construct_event.return_value = {
            "id": "evt_sub_delete",
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_test_delete", "status": "canceled"}},
        }

        response = self.client.post(
            reverse("monetization:stripe_webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test",
        )

        self.assertEqual(response.status_code, 200)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, ChannelMembershipSubscription.Status.ENDED)
        self.assertIsNotNone(subscription.ended_at)


class StripeProviderDisabledTests(TestCase):
    @override_settings(MONETIZATION_PAYMENT_PROVIDER="sandbox", STRIPE_SECRET_KEY="")
    def test_stripe_webhook_is_not_exposed_when_provider_disabled(self):
        response = self.client.post(reverse("monetization:stripe_webhook"), data=b"{}", content_type="application/json")
        self.assertEqual(response.status_code, 404)
