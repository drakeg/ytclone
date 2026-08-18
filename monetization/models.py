from django.conf import settings
from django.db import models


class CreatorMonetizationAccount(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    channel = models.OneToOneField(
        "video.Channel",
        on_delete=models.CASCADE,
        related_name="monetization_account",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    payouts_enabled = models.BooleanField(default=False)
    provider = models.CharField(max_length=32, blank=True)
    provider_account_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_ready_to_earn(self):
        return (
            self.status == self.Status.ACTIVE
            and self.terms_accepted_at is not None
            and self.payouts_enabled
        )

    def __str__(self):
        return f"{self.channel} monetization"


class MembershipTier(models.Model):
    monetization_account = models.ForeignKey(
        CreatorMonetizationAccount,
        on_delete=models.CASCADE,
        related_name="membership_tiers",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price_minor = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["monetization_account", "name"],
                name="unique_membership_tier_name_per_channel",
            )
        ]

    def __str__(self):
        return f"{self.monetization_account.channel}: {self.name}"


class ChannelMembershipSubscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past due"
        CANCELED = "canceled", "Canceled"
        ENDED = "ended", "Ended"

    tier = models.ForeignKey(
        MembershipTier,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="paid_channel_memberships",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    provider_subscription_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tier", "subscriber"],
                name="unique_subscriber_per_membership_tier",
            )
        ]

    def __str__(self):
        return f"{self.subscriber} -> {self.tier}"


class MonetizationTransaction(models.Model):
    class Kind(models.TextChoices):
        TIP = "tip", "Tip"
        MEMBERSHIP = "membership", "Membership"
        REFUND = "refund", "Refund"
        REVERSAL = "reversal", "Reversal"
        PAYOUT = "payout", "Payout"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        REVERSED = "reversed", "Reversed"

    monetization_account = models.ForeignKey(
        CreatorMonetizationAccount,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="monetization_payments",
    )
    membership_subscription = models.ForeignKey(
        ChannelMembershipSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    currency = models.CharField(max_length=3, default="USD")
    gross_amount_minor = models.PositiveIntegerField()
    platform_fee_minor = models.PositiveIntegerField(default=0)
    provider_fee_minor = models.PositiveIntegerField(default=0)
    creator_net_minor = models.IntegerField(default=0)
    platform_fee_bps = models.PositiveIntegerField(default=0)
    idempotency_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
    )
    provider_payment_id = models.CharField(max_length=255, blank=True)
    provider_event_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"{self.kind}: {self.gross_amount_minor} {self.currency}"
