from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from video.models import Channel
from .models import (
    ChannelMembershipSubscription,
    CreatorMonetizationAccount,
    MembershipTier,
    MonetizationTransaction,
)


@override_settings(
    MONETIZATION_PAYMENT_PROVIDER="stripe",
    STRIPE_SECRET_KEY="sk_test_example",
    STRIPE_WEBHOOK_SECRET="whsec_example",
    MONETIZATION_PLATFORM_FEE_BPS=1000,
)
class StripeAccountingWebhookTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="acctcreator", password="password123")
        self.viewer = User.objects.create_user(username="acctviewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Accounting Channel")
        self.account = CreatorMonetizationAccount.objects.create(
            channel=self.channel,
            status=CreatorMonetizationAccount.Status.ACTIVE,
            terms_accepted_at=timezone.now(),
            payouts_enabled=True,
            provider="stripe",
            provider_account_id="acct_test_accounting",
        )
        self.tier = MembershipTier.objects.create(
            monetization_account=self.account,
            name="Supporter",
            price_minor=500,
            currency="USD",
        )
        self.subscription = ChannelMembershipSubscription.objects.create(
            tier=self.tier,
            subscriber=self.viewer,
            provider_subscription_id="sub_test_accounting",
        )
        self.url = reverse("monetization:stripe_webhook")

    def post_event(self, event):
        with patch("monetization.stripe_views.stripe_gateway.construct_webhook_event", return_value=event):
            return self.client.post(
                self.url,
                data=b"{}",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="test",
            )

    def test_recurring_invoice_paid_records_renewal_once(self):
        event = {
            "id": "evt_invoice_paid_1",
            "type": "invoice.paid",
            "data": {"object": {
                "id": "in_test_renewal_1",
                "subscription": self.subscription.provider_subscription_id,
                "billing_reason": "subscription_cycle",
                "amount_paid": 500,
                "currency": "usd",
                "metadata": {"ytclone_platform_fee_bps": "1000"},
            }},
        }
        self.post_event(event)
        self.post_event(event)

        transaction = MonetizationTransaction.objects.get(provider_event_id="evt_invoice_paid_1")
        self.assertEqual(transaction.status, MonetizationTransaction.Status.SUCCEEDED)
        self.assertEqual(transaction.gross_amount_minor, 500)
        self.assertEqual(transaction.platform_fee_minor, 50)
        self.assertEqual(transaction.creator_net_minor, 450)
        self.assertEqual(MonetizationTransaction.objects.filter(provider_event_id="evt_invoice_paid_1").count(), 1)

    def test_failed_invoice_marks_membership_past_due_and_records_failed_attempt(self):
        response = self.post_event({
            "id": "evt_invoice_failed_1",
            "type": "invoice.payment_failed",
            "data": {"object": {
                "id": "in_test_failed_1",
                "subscription": self.subscription.provider_subscription_id,
                "amount_due": 500,
                "currency": "usd",
            }},
        })

        self.assertEqual(response.status_code, 200)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, ChannelMembershipSubscription.Status.PAST_DUE)
        transaction = MonetizationTransaction.objects.get(provider_event_id="evt_invoice_failed_1")
        self.assertEqual(transaction.status, MonetizationTransaction.Status.FAILED)
        self.assertEqual(transaction.creator_net_minor, 0)
        self.assertEqual(transaction.platform_fee_minor, 0)

    def test_later_success_recovers_past_due_membership(self):
        self.subscription.status = ChannelMembershipSubscription.Status.PAST_DUE
        self.subscription.save(update_fields=["status"])
        self.post_event({
            "id": "evt_invoice_recovered_1",
            "type": "invoice.paid",
            "data": {"object": {
                "id": "in_test_recovered_1",
                "subscription": self.subscription.provider_subscription_id,
                "billing_reason": "subscription_cycle",
                "amount_paid": 500,
                "currency": "usd",
            }},
        })
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, ChannelMembershipSubscription.Status.ACTIVE)

    def test_initial_subscription_invoice_does_not_duplicate_checkout_ledger(self):
        MonetizationTransaction.objects.create(
            monetization_account=self.account,
            payer=self.viewer,
            membership_subscription=self.subscription,
            kind=MonetizationTransaction.Kind.MEMBERSHIP,
            status=MonetizationTransaction.Status.SUCCEEDED,
            gross_amount_minor=500,
            platform_fee_minor=50,
            creator_net_minor=450,
            platform_fee_bps=1000,
            provider_payment_id=self.subscription.provider_subscription_id,
            provider_event_id="evt_checkout_initial",
        )
        self.post_event({
            "id": "evt_invoice_initial",
            "type": "invoice.paid",
            "data": {"object": {
                "id": "in_test_initial",
                "subscription": self.subscription.provider_subscription_id,
                "billing_reason": "subscription_create",
                "amount_paid": 500,
                "currency": "usd",
            }},
        })
        self.assertFalse(MonetizationTransaction.objects.filter(provider_event_id="evt_invoice_initial").exists())

    def test_terminal_subscription_is_not_resurrected_by_late_invoice(self):
        self.subscription.status = ChannelMembershipSubscription.Status.ENDED
        self.subscription.ended_at = timezone.now()
        self.subscription.save(update_fields=["status", "ended_at"])
        self.post_event({
            "id": "evt_late_invoice",
            "type": "invoice.paid",
            "data": {"object": {
                "id": "in_test_late",
                "subscription": self.subscription.provider_subscription_id,
                "billing_reason": "subscription_cycle",
                "amount_paid": 500,
                "currency": "usd",
            }},
        })
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, ChannelMembershipSubscription.Status.ENDED)

    def test_charge_refund_creates_creator_refund_and_platform_reversal_once(self):
        original = MonetizationTransaction.objects.create(
            monetization_account=self.account,
            payer=self.viewer,
            membership_subscription=self.subscription,
            kind=MonetizationTransaction.Kind.MEMBERSHIP,
            status=MonetizationTransaction.Status.SUCCEEDED,
            gross_amount_minor=500,
            platform_fee_minor=50,
            creator_net_minor=450,
            platform_fee_bps=1000,
            provider_payment_id="in_test_refundable",
            provider_event_id="evt_original_payment",
        )
        event = {
            "id": "evt_charge_refunded_1",
            "type": "charge.refunded",
            "data": {"object": {
                "id": "ch_test_refund",
                "invoice": original.provider_payment_id,
                "amount_refunded": 500,
                "currency": "usd",
            }},
        }
        self.post_event(event)
        self.post_event(event)

        refund = MonetizationTransaction.objects.get(provider_event_id="evt_charge_refunded_1:refund")
        reversal = MonetizationTransaction.objects.get(provider_event_id="evt_charge_refunded_1:reversal")
        self.assertEqual(refund.kind, MonetizationTransaction.Kind.REFUND)
        self.assertEqual(refund.creator_net_minor, -450)
        self.assertEqual(reversal.kind, MonetizationTransaction.Kind.REVERSAL)
        self.assertEqual(reversal.platform_fee_minor, -50)
        self.assertEqual(MonetizationTransaction.objects.filter(provider_event_id__startswith="evt_charge_refunded_1").count(), 2)
