from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from video.models import Channel
from .models import (
    ChannelMembershipSubscription,
    CreatorMonetizationAccount,
    MembershipTier,
    MonetizationTransaction,
)


def field(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def metadata(obj):
    value = field(obj, "metadata", {})
    return dict(value or {})


def nested(obj, *names, default=None):
    current = obj
    for name in names:
        current = field(current, name, None)
        if current is None:
            return default
    return current


def invoice_subscription_id(invoice):
    direct = field(invoice, "subscription", None)
    if direct:
        return str(direct)
    parent_id = nested(invoice, "parent", "subscription_details", "subscription", default=None)
    return str(parent_id or "")


def invoice_metadata(invoice):
    direct = metadata(invoice)
    if direct:
        return direct
    parent_meta = nested(invoice, "parent", "subscription_details", "metadata", default={})
    return dict(parent_meta or {})


def _fee_bps(meta):
    try:
        return int(meta.get("ytclone_platform_fee_bps", settings.MONETIZATION_PLATFORM_FEE_BPS))
    except (TypeError, ValueError):
        return settings.MONETIZATION_PLATFORM_FEE_BPS


def handle_checkout_completed(event_id, session):
    meta = metadata(session)
    kind = meta.get("ytclone_kind")
    payer = get_user_model().objects.filter(pk=meta.get("ytclone_payer_id")).first()
    if not payer:
        return

    if kind == "tip":
        channel = Channel.objects.filter(pk=meta.get("ytclone_channel_id")).first()
        account = (
            CreatorMonetizationAccount.objects.filter(channel=channel, provider="stripe").first()
            if channel
            else None
        )
        gross = int(meta.get("ytclone_gross_minor", 0) or 0)
        fee = int(meta.get("ytclone_platform_fee_minor", 0) or 0)
        if account and gross > 0:
            MonetizationTransaction.objects.get_or_create(
                provider_event_id=event_id,
                defaults={
                    "monetization_account": account,
                    "payer": payer,
                    "kind": MonetizationTransaction.Kind.TIP,
                    "status": MonetizationTransaction.Status.SUCCEEDED,
                    "currency": str(field(session, "currency", "usd") or "usd").upper(),
                    "gross_amount_minor": gross,
                    "platform_fee_minor": fee,
                    "creator_net_minor": gross - fee,
                    "platform_fee_bps": settings.MONETIZATION_PLATFORM_FEE_BPS,
                    "provider_payment_id": str(field(session, "payment_intent", "") or ""),
                },
            )
        return

    if kind != "membership":
        return
    tier = MembershipTier.objects.select_related("monetization_account").filter(
        pk=meta.get("ytclone_tier_id")
    ).first()
    provider_subscription_id = str(field(session, "subscription", "") or "")
    if not tier or not provider_subscription_id:
        return
    existing_active = ChannelMembershipSubscription.objects.filter(
        subscriber=payer,
        status=ChannelMembershipSubscription.Status.ACTIVE,
        tier__monetization_account=tier.monetization_account,
    ).first()
    if existing_active and (
        existing_active.tier_id != tier.pk
        or existing_active.provider_subscription_id != provider_subscription_id
    ):
        return
    subscription, unused = ChannelMembershipSubscription.objects.get_or_create(
        tier=tier,
        subscriber=payer,
    )
    subscription.status = ChannelMembershipSubscription.Status.ACTIVE
    subscription.provider_subscription_id = provider_subscription_id
    subscription.canceled_at = None
    subscription.ended_at = None
    subscription.save()
    fee_bps = _fee_bps(meta)
    fee = (tier.price_minor * fee_bps) // 10000
    MonetizationTransaction.objects.get_or_create(
        provider_event_id=event_id,
        defaults={
            "monetization_account": tier.monetization_account,
            "payer": payer,
            "membership_subscription": subscription,
            "kind": MonetizationTransaction.Kind.MEMBERSHIP,
            "status": MonetizationTransaction.Status.SUCCEEDED,
            "currency": tier.currency,
            "gross_amount_minor": tier.price_minor,
            "platform_fee_minor": fee,
            "creator_net_minor": tier.price_minor - fee,
            "platform_fee_bps": fee_bps,
            "provider_payment_id": provider_subscription_id,
        },
    )


def _subscription_for_invoice(invoice):
    provider_subscription_id = invoice_subscription_id(invoice)
    subscription = None
    if provider_subscription_id:
        subscription = (
            ChannelMembershipSubscription.objects.select_related(
                "tier", "tier__monetization_account", "subscriber"
            )
            .filter(provider_subscription_id=provider_subscription_id)
            .first()
        )
    if subscription:
        return subscription

    meta = invoice_metadata(invoice)
    tier_id = meta.get("ytclone_tier_id")
    payer_id = meta.get("ytclone_payer_id")
    if not tier_id or not payer_id or not provider_subscription_id:
        return None
    tier = MembershipTier.objects.select_related("monetization_account").filter(pk=tier_id).first()
    payer = get_user_model().objects.filter(pk=payer_id).first()
    if not tier or not payer:
        return None
    subscription, unused = ChannelMembershipSubscription.objects.get_or_create(
        tier=tier,
        subscriber=payer,
    )
    if subscription.provider_subscription_id and subscription.provider_subscription_id != provider_subscription_id:
        return None
    subscription.provider_subscription_id = provider_subscription_id
    subscription.save(update_fields=["provider_subscription_id"])
    return subscription


def handle_invoice_paid(event_id, invoice):
    subscription = _subscription_for_invoice(invoice)
    if not subscription:
        return

    if subscription.status != ChannelMembershipSubscription.Status.ENDED:
        subscription.status = ChannelMembershipSubscription.Status.ACTIVE
        subscription.ended_at = None
        subscription.save(update_fields=["status", "ended_at"])

    if field(invoice, "billing_reason", "") == "subscription_create":
        return

    amount_paid = int(field(invoice, "amount_paid", 0) or 0)
    if amount_paid <= 0:
        return
    meta = invoice_metadata(invoice)
    fee_bps = _fee_bps(meta)
    fee = (amount_paid * fee_bps) // 10000
    MonetizationTransaction.objects.get_or_create(
        provider_event_id=event_id,
        defaults={
            "monetization_account": subscription.tier.monetization_account,
            "payer": subscription.subscriber,
            "membership_subscription": subscription,
            "kind": MonetizationTransaction.Kind.MEMBERSHIP,
            "status": MonetizationTransaction.Status.SUCCEEDED,
            "currency": str(field(invoice, "currency", subscription.tier.currency) or subscription.tier.currency).upper(),
            "gross_amount_minor": amount_paid,
            "platform_fee_minor": fee,
            "creator_net_minor": amount_paid - fee,
            "platform_fee_bps": fee_bps,
            "provider_payment_id": str(field(invoice, "id", "") or ""),
        },
    )


def handle_invoice_failed(event_id, invoice):
    subscription = _subscription_for_invoice(invoice)
    if not subscription or subscription.status == ChannelMembershipSubscription.Status.ENDED:
        return
    subscription.status = ChannelMembershipSubscription.Status.PAST_DUE
    subscription.save(update_fields=["status"])

    amount_due = int(field(invoice, "amount_due", 0) or 0)
    MonetizationTransaction.objects.get_or_create(
        provider_event_id=event_id,
        defaults={
            "monetization_account": subscription.tier.monetization_account,
            "payer": subscription.subscriber,
            "membership_subscription": subscription,
            "kind": MonetizationTransaction.Kind.MEMBERSHIP,
            "status": MonetizationTransaction.Status.FAILED,
            "currency": str(field(invoice, "currency", subscription.tier.currency) or subscription.tier.currency).upper(),
            "gross_amount_minor": max(amount_due, 0),
            "platform_fee_minor": 0,
            "creator_net_minor": 0,
            "platform_fee_bps": _fee_bps(invoice_metadata(invoice)),
            "provider_payment_id": str(field(invoice, "id", "") or ""),
        },
    )


@transaction.atomic
def handle_charge_refunded(event_id, charge):
    candidate_ids = [
        str(field(charge, "id", "") or ""),
        str(field(charge, "payment_intent", "") or ""),
        str(field(charge, "invoice", "") or ""),
    ]
    candidate_ids = [value for value in candidate_ids if value]
    if not candidate_ids:
        return
    original = (
        MonetizationTransaction.objects.select_for_update().select_related("payer", "membership_subscription")
        .filter(provider_payment_id__in=candidate_ids, status=MonetizationTransaction.Status.SUCCEEDED)
        .exclude(kind__in=[MonetizationTransaction.Kind.REFUND, MonetizationTransaction.Kind.REVERSAL])
        .order_by("-created_at")
        .first()
    )
    if not original or original.gross_amount_minor <= 0:
        return

    reported_refund = int(field(charge, "amount_refunded", 0) or 0)
    if reported_refund <= 0:
        return
    reported_refund = min(reported_refund, original.gross_amount_minor)
    refund_provider_id = str(field(charge, "id", "") or original.provider_payment_id)
    recorded = MonetizationTransaction.objects.filter(
        monetization_account=original.monetization_account,
        kind=MonetizationTransaction.Kind.REFUND,
        status=MonetizationTransaction.Status.SUCCEEDED,
        provider_payment_id=refund_provider_id,
    ).aggregate(total=Sum("gross_amount_minor"))["total"] or 0
    refund_amount = reported_refund - recorded
    if refund_amount <= 0:
        return

    total_platform_refund = round(
        original.platform_fee_minor * reported_refund / original.gross_amount_minor
    )
    recorded_platform_refund = -(
        MonetizationTransaction.objects.filter(
            monetization_account=original.monetization_account,
            kind=MonetizationTransaction.Kind.REVERSAL,
            status=MonetizationTransaction.Status.SUCCEEDED,
            provider_payment_id=refund_provider_id,
        ).aggregate(total=Sum("platform_fee_minor"))["total"]
        or 0
    )
    platform_refund = max(total_platform_refund - recorded_platform_refund, 0)
    creator_refund = refund_amount - platform_refund

    MonetizationTransaction.objects.get_or_create(
        provider_event_id=f"{event_id}:refund",
        defaults={
            "monetization_account": original.monetization_account,
            "payer": original.payer,
            "membership_subscription": original.membership_subscription,
            "kind": MonetizationTransaction.Kind.REFUND,
            "status": MonetizationTransaction.Status.SUCCEEDED,
            "currency": original.currency,
            "gross_amount_minor": refund_amount,
            "platform_fee_minor": 0,
            "creator_net_minor": -creator_refund,
            "platform_fee_bps": original.platform_fee_bps,
            "provider_payment_id": refund_provider_id,
        },
    )
    MonetizationTransaction.objects.get_or_create(
        provider_event_id=f"{event_id}:reversal",
        defaults={
            "monetization_account": original.monetization_account,
            "payer": original.payer,
            "membership_subscription": original.membership_subscription,
            "kind": MonetizationTransaction.Kind.REVERSAL,
            "status": MonetizationTransaction.Status.SUCCEEDED,
            "currency": original.currency,
            "gross_amount_minor": 0,
            "platform_fee_minor": -platform_refund,
            "creator_net_minor": 0,
            "platform_fee_bps": original.platform_fee_bps,
            "provider_payment_id": refund_provider_id,
        },
    )


def handle_subscription_state(event_type, subscription_obj):
    provider_subscription_id = str(field(subscription_obj, "id", "") or "")
    subscription = ChannelMembershipSubscription.objects.filter(
        provider_subscription_id=provider_subscription_id
    ).first()
    if not subscription:
        return
    stripe_status = str(field(subscription_obj, "status", "") or "")
    if event_type == "customer.subscription.deleted" or stripe_status in {
        "canceled",
        "unpaid",
        "incomplete_expired",
    }:
        subscription.status = ChannelMembershipSubscription.Status.ENDED
        subscription.ended_at = timezone.now()
        subscription.save(update_fields=["status", "ended_at"])
    elif stripe_status == "past_due":
        if subscription.status != ChannelMembershipSubscription.Status.ENDED:
            subscription.status = ChannelMembershipSubscription.Status.PAST_DUE
            subscription.save(update_fields=["status"])
    elif stripe_status in {"active", "trialing"}:
        if subscription.status != ChannelMembershipSubscription.Status.ENDED:
            subscription.status = ChannelMembershipSubscription.Status.ACTIVE
            subscription.ended_at = None
            subscription.save(update_fields=["status", "ended_at"])


def dispatch(event):
    event_id = str(field(event, "id", "") or "")
    event_type = str(field(event, "type", "") or "")
    obj = field(field(event, "data", {}), "object", {})
    if event_type == "checkout.session.completed":
        handle_checkout_completed(event_id, obj)
    elif event_type == "invoice.paid":
        handle_invoice_paid(event_id, obj)
    elif event_type == "invoice.payment_failed":
        handle_invoice_failed(event_id, obj)
    elif event_type == "charge.refunded":
        handle_charge_refunded(event_id, obj)
    elif event_type in {"customer.subscription.updated", "customer.subscription.deleted"}:
        handle_subscription_state(event_type, obj)
