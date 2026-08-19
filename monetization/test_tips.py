from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from video.models import Channel

from .models import CreatorMonetizationAccount, MonetizationTransaction


@override_settings(MONETIZATION_PLATFORM_FEE_BPS=1000)
class SandboxTipTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="tipcreator", password="password123")
        self.viewer = User.objects.create_user(username="tipviewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Tip Channel")
        self.account = CreatorMonetizationAccount.objects.create(
            channel=self.channel,
            status=CreatorMonetizationAccount.Status.ACTIVE,
            terms_accepted_at=timezone.now(),
            payouts_enabled=True,
            provider="test",
            provider_account_id="acct_test_tip",
        )

    def test_viewer_can_send_sandbox_tip_with_platform_split(self):
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("monetization:send_sandbox_tip", args=[self.channel.pk]),
            {"amount": "10.00"},
        )

        self.assertRedirects(response, reverse("channel_detail", args=[self.channel.pk]))
        transaction = MonetizationTransaction.objects.get(kind=MonetizationTransaction.Kind.TIP)
        self.assertEqual(transaction.gross_amount_minor, 1000)
        self.assertEqual(transaction.platform_fee_minor, 100)
        self.assertEqual(transaction.creator_net_minor, 900)
        self.assertEqual(transaction.platform_fee_bps, 1000)
        self.assertEqual(transaction.payer, self.viewer)
        self.assertTrue(transaction.provider_payment_id.startswith("test_pay_"))

    def test_channel_owner_cannot_tip_self(self):
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("monetization:send_sandbox_tip", args=[self.channel.pk]),
            {"amount": "5.00"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(MonetizationTransaction.objects.exists())

    def test_tip_requires_ready_monetization_account(self):
        self.account.payouts_enabled = False
        self.account.save(update_fields=["payouts_enabled"])
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("monetization:send_sandbox_tip", args=[self.channel.pk]),
            {"amount": "5.00"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(MonetizationTransaction.objects.exists())

    def test_invalid_tip_amount_does_not_create_transaction(self):
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("monetization:send_sandbox_tip", args=[self.channel.pk]),
            {"amount": "0.25"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(MonetizationTransaction.objects.exists())

    def test_ready_channel_shows_tip_action_to_viewer(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("channel_detail", args=[self.channel.pk]))

        self.assertContains(response, reverse("monetization:tip_form", args=[self.channel.pk]))
        self.assertContains(response, "Tip this creator")
