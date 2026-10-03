from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from video.models import Channel

from .accounting import payout_readiness_summary
from .models import (
    CreatorMonetizationAccount,
    MembershipTier,
    MonetizationTransaction,
)


class MonetizationDomainTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="newcreator", password="password123"
        )
        self.channel = Channel.objects.create(
            owner=self.creator,
            name="Brand New Channel",
            description="No audience yet",
        )

    def test_brand_new_channel_can_be_ready_to_earn_without_audience_thresholds(self):
        account = CreatorMonetizationAccount.objects.create(
            channel=self.channel,
            status=CreatorMonetizationAccount.Status.ACTIVE,
            terms_accepted_at=timezone.now(),
            payouts_enabled=True,
            provider="test",
            provider_account_id="acct_test_creator",
        )

        self.assertEqual(self.channel.subscribers.count(), 0)
        self.assertFalse(self.channel.videos.exists())
        self.assertTrue(account.is_ready_to_earn)

    def test_pending_onboarding_is_not_ready_to_earn(self):
        account = CreatorMonetizationAccount.objects.create(channel=self.channel)

        self.assertFalse(account.is_ready_to_earn)

    def test_membership_tier_uses_integer_minor_units(self):
        account = CreatorMonetizationAccount.objects.create(channel=self.channel)
        tier = MembershipTier.objects.create(
            monetization_account=account,
            name="Supporter",
            description="Support the channel",
            price_minor=499,
            currency="USD",
        )

        self.assertEqual(tier.price_minor, 499)

    def test_transaction_snapshots_platform_revenue_split(self):
        account = CreatorMonetizationAccount.objects.create(channel=self.channel)
        viewer = User.objects.create_user(username="viewer", password="password123")

        transaction = MonetizationTransaction.objects.create(
            monetization_account=account,
            payer=viewer,
            kind=MonetizationTransaction.Kind.TIP,
            status=MonetizationTransaction.Status.SUCCEEDED,
            gross_amount_minor=1000,
            platform_fee_minor=100,
            provider_fee_minor=59,
            creator_net_minor=841,
            platform_fee_bps=1000,
            idempotency_key="tip-test-1",
        )

        self.assertEqual(transaction.gross_amount_minor, 1000)
        self.assertEqual(transaction.platform_fee_minor, 100)
        self.assertEqual(transaction.creator_net_minor, 841)
        self.assertEqual(transaction.platform_fee_bps, 1000)


class PayoutReadinessSummaryTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="payoutcreator", password="password123")
        self.viewer = User.objects.create_user(username="payoutviewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Payout Ready Channel")
        self.account = CreatorMonetizationAccount.objects.create(
            channel=self.channel,
            status=CreatorMonetizationAccount.Status.ACTIVE,
            terms_accepted_at=timezone.now(),
            payouts_enabled=True,
            provider="test",
            provider_account_id="acct_test_payout",
        )

    def transaction(self, *, kind, status, creator_net_minor):
        return MonetizationTransaction.objects.create(
            monetization_account=self.account,
            payer=self.viewer,
            kind=kind,
            status=status,
            gross_amount_minor=max(abs(creator_net_minor), 0),
            platform_fee_minor=0,
            provider_fee_minor=0,
            creator_net_minor=creator_net_minor,
            platform_fee_bps=0,
        )

    def test_summary_distinguishes_earned_pending_refunded_paid_and_available(self):
        self.transaction(
            kind=MonetizationTransaction.Kind.TIP,
            status=MonetizationTransaction.Status.SUCCEEDED,
            creator_net_minor=900,
        )
        self.transaction(
            kind=MonetizationTransaction.Kind.MEMBERSHIP,
            status=MonetizationTransaction.Status.SUCCEEDED,
            creator_net_minor=450,
        )
        self.transaction(
            kind=MonetizationTransaction.Kind.MEMBERSHIP,
            status=MonetizationTransaction.Status.PENDING,
            creator_net_minor=450,
        )
        self.transaction(
            kind=MonetizationTransaction.Kind.REFUND,
            status=MonetizationTransaction.Status.SUCCEEDED,
            creator_net_minor=-225,
        )
        self.transaction(
            kind=MonetizationTransaction.Kind.REVERSAL,
            status=MonetizationTransaction.Status.SUCCEEDED,
            creator_net_minor=-25,
        )
        self.transaction(
            kind=MonetizationTransaction.Kind.PAYOUT,
            status=MonetizationTransaction.Status.SUCCEEDED,
            creator_net_minor=-500,
        )
        self.transaction(
            kind=MonetizationTransaction.Kind.TIP,
            status=MonetizationTransaction.Status.FAILED,
            creator_net_minor=999,
        )

        summary = payout_readiness_summary(self.account)

        self.assertEqual(summary.earned_minor, 1350)
        self.assertEqual(summary.pending_minor, 450)
        self.assertEqual(summary.refunded_reversed_minor, 250)
        self.assertEqual(summary.paid_out_minor, 500)
        self.assertEqual(summary.available_minor, 600)

    def test_creator_dashboard_shows_payout_readiness_without_creating_payout(self):
        self.transaction(
            kind=MonetizationTransaction.Kind.TIP,
            status=MonetizationTransaction.Status.SUCCEEDED,
            creator_net_minor=900,
        )
        self.transaction(
            kind=MonetizationTransaction.Kind.PAYOUT,
            status=MonetizationTransaction.Status.SUCCEEDED,
            creator_net_minor=-400,
        )
        self.client.force_login(self.creator)

        response = self.client.get(
            reverse("monetization:creator_dashboard", args=[self.channel.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Available")
        self.assertContains(response, "$5.00")
        self.assertContains(response, "Paid out")
        self.assertContains(response, "$4.00")
        self.assertEqual(
            MonetizationTransaction.objects.filter(
                monetization_account=self.account,
                kind=MonetizationTransaction.Kind.PAYOUT,
            ).count(),
            1,
        )
