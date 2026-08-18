from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from video.models import Channel

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
