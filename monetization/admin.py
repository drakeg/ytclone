from django.contrib import admin

from .models import (
    ChannelMembershipSubscription,
    CreatorMonetizationAccount,
    MembershipTier,
    MonetizationTransaction,
)


@admin.register(CreatorMonetizationAccount)
class CreatorMonetizationAccountAdmin(admin.ModelAdmin):
    list_display = ("channel", "status", "payouts_enabled", "provider", "updated_at")
    list_filter = ("status", "payouts_enabled", "provider")
    search_fields = ("channel__name", "channel__owner__username", "provider_account_id")


@admin.register(MembershipTier)
class MembershipTierAdmin(admin.ModelAdmin):
    list_display = ("name", "monetization_account", "price_minor", "currency", "is_active")
    list_filter = ("currency", "is_active")
    search_fields = ("name", "monetization_account__channel__name")


@admin.register(ChannelMembershipSubscription)
class ChannelMembershipSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("subscriber", "tier", "status", "started_at")
    list_filter = ("status",)
    search_fields = ("subscriber__username", "tier__name", "tier__monetization_account__channel__name")


@admin.register(MonetizationTransaction)
class MonetizationTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "kind",
        "status",
        "monetization_account",
        "gross_amount_minor",
        "platform_fee_minor",
        "creator_net_minor",
        "currency",
        "created_at",
    )
    list_filter = ("kind", "status", "currency")
    search_fields = (
        "monetization_account__channel__name",
        "payer__username",
        "provider_payment_id",
        "provider_event_id",
        "idempotency_key",
    )
    readonly_fields = (
        "monetization_account",
        "payer",
        "membership_subscription",
        "kind",
        "status",
        "currency",
        "gross_amount_minor",
        "platform_fee_minor",
        "provider_fee_minor",
        "creator_net_minor",
        "platform_fee_bps",
        "idempotency_key",
        "provider_payment_id",
        "provider_event_id",
        "created_at",
    )
