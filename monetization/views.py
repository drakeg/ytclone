import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from video.models import Channel

from . import stripe_gateway
from .forms import MembershipTierForm, TipForm
from .models import (
    ChannelMembershipSubscription,
    CreatorMonetizationAccount,
    MembershipTier,
    MonetizationTransaction,
)


def _money(minor):
    return f"{minor / 100:.2f}"


def _owned_channel(user, pk):
    return get_object_or_404(Channel, pk=pk, owner=user)


def _record_sandbox_payment(*, account, payer, kind, gross_amount_minor, currency="USD", membership_subscription=None):
    fee_bps = settings.MONETIZATION_PLATFORM_FEE_BPS
    platform_fee_minor = (gross_amount_minor * fee_bps) // 10000
    return MonetizationTransaction.objects.create(
        monetization_account=account,
        payer=payer,
        membership_subscription=membership_subscription,
        kind=kind,
        status=MonetizationTransaction.Status.SUCCEEDED,
        currency=currency,
        gross_amount_minor=gross_amount_minor,
        platform_fee_minor=platform_fee_minor,
        provider_fee_minor=0,
        creator_net_minor=gross_amount_minor - platform_fee_minor,
        platform_fee_bps=fee_bps,
        idempotency_key=f"sandbox-{kind}-{uuid.uuid4()}",
        provider_payment_id=f"test_pay_{uuid.uuid4().hex}",
    )


def _absolute(request, route_name, *args):
    return request.build_absolute_uri(reverse(route_name, args=args))


def _meta(obj):
    value = getattr(obj, "metadata", None)
    if value is None and isinstance(obj, dict):
        value = obj.get("metadata")
    return dict(value or {})


def _field(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


@login_required
def creator_dashboard(request, pk):
    channel = _owned_channel(request.user, pk)
    account = CreatorMonetizationAccount.objects.filter(channel=channel).first()
    tiers = list(account.membership_tiers.order_by("price_minor", "name")) if account else []
    transactions = list(account.transactions.select_related("payer").all()[:20] if account else [])
    creator_net_minor = 0
    platform_fee_minor = 0
    if account:
        totals = account.transactions.filter(status=MonetizationTransaction.Status.SUCCEEDED).aggregate(
            creator_net=Sum("creator_net_minor"), platform_fee=Sum("platform_fee_minor")
        )
        creator_net_minor = totals["creator_net"] or 0
        platform_fee_minor = totals["platform_fee"] or 0

    for tier in tiers:
        tier.price_display = _money(tier.price_minor)
        tier.active_members = tier.subscriptions.filter(status=ChannelMembershipSubscription.Status.ACTIVE).count()
    for transaction in transactions:
        transaction.gross_display = _money(transaction.gross_amount_minor)
        transaction.creator_net_display = _money(transaction.creator_net_minor)

    return render(request, "monetization/creator_dashboard.html", {
        "channel": channel,
        "account": account,
        "tiers": tiers,
        "transactions": transactions,
        "creator_net_display": _money(creator_net_minor),
        "platform_fee_display": _money(platform_fee_minor),
        "platform_fee_percent": settings.MONETIZATION_PLATFORM_FEE_BPS / 100,
        "payment_provider": settings.MONETIZATION_PAYMENT_PROVIDER,
        "stripe_enabled": stripe_gateway.stripe_enabled(),
    })


@login_required
@require_POST
def enable_sandbox(request, pk):
    channel = _owned_channel(request.user, pk)
    account, unused = CreatorMonetizationAccount.objects.get_or_create(channel=channel)
    account.status = CreatorMonetizationAccount.Status.ACTIVE
    account.terms_accepted_at = account.terms_accepted_at or timezone.now()
    account.payouts_enabled = True
    account.provider = "test"
    account.provider_account_id = account.provider_account_id or f"acct_test_{channel.pk}"
    account.save()
    return redirect("monetization:creator_dashboard", pk=channel.pk)


@login_required
@require_POST
def start_stripe_onboarding(request, pk):
    if not stripe_gateway.stripe_enabled():
        return HttpResponseForbidden("Stripe test mode is not enabled.")
    channel = _owned_channel(request.user, pk)
    account, unused = CreatorMonetizationAccount.objects.get_or_create(channel=channel)
    if not account.provider_account_id or account.provider != "stripe":
        account.provider_account_id = stripe_gateway.create_connected_account(email=request.user.email or None)
        account.provider = "stripe"
        account.status = CreatorMonetizationAccount.Status.PENDING
        account.payouts_enabled = False
        account.terms_accepted_at = account.terms_accepted_at or timezone.now()
        account.save()
    link = stripe_gateway.create_account_onboarding_link(
        account_id=account.provider_account_id,
        refresh_url=_absolute(request, "monetization:stripe_onboarding_refresh", channel.pk),
        return_url=_absolute(request, "monetization:stripe_onboarding_return", channel.pk),
    )
    return redirect(link)


@login_required
def stripe_onboarding_refresh(request, pk):
    return start_stripe_onboarding(request, pk)


@login_required
def stripe_onboarding_return(request, pk):
    channel = _owned_channel(request.user, pk)
    account = get_object_or_404(CreatorMonetizationAccount, channel=channel, provider="stripe")
    stripe_account = stripe_gateway.retrieve_connected_account(account.provider_account_id)
    account.payouts_enabled = bool(_field(stripe_account, "payouts_enabled", False))
    charges_enabled = bool(_field(stripe_account, "charges_enabled", False))
    account.status = CreatorMonetizationAccount.Status.ACTIVE if charges_enabled and account.payouts_enabled else CreatorMonetizationAccount.Status.PENDING
    account.save(update_fields=["payouts_enabled", "status", "updated_at"])
    return redirect("monetization:creator_dashboard", pk=channel.pk)


@login_required
def tier_create(request, pk):
    channel = _owned_channel(request.user, pk)
    account = get_object_or_404(CreatorMonetizationAccount, channel=channel)
    if not account.is_ready_to_earn:
        return HttpResponseForbidden("Enable channel monetization before creating tiers.")
    form = MembershipTierForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        MembershipTier.objects.create(monetization_account=account, name=form.cleaned_data["name"], description=form.cleaned_data["description"], price_minor=form.price_minor(), currency="USD")
        return redirect("monetization:creator_dashboard", pk=channel.pk)
    return render(request, "monetization/tier_form.html", {"channel": channel, "form": form})


@login_required
def tier_edit(request, tier_pk):
    tier = get_object_or_404(MembershipTier.objects.select_related("monetization_account__channel"), pk=tier_pk, monetization_account__channel__owner=request.user)
    channel = tier.monetization_account.channel
    initial = {"name": tier.name, "description": tier.description, "monthly_price": _money(tier.price_minor)}
    form = MembershipTierForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        tier.name = form.cleaned_data["name"]
        tier.description = form.cleaned_data["description"]
        tier.price_minor = form.price_minor()
        tier.save(update_fields=["name", "description", "price_minor", "updated_at"])
        return redirect("monetization:creator_dashboard", pk=channel.pk)
    return render(request, "monetization/tier_form.html", {"channel": channel, "form": form, "tier": tier})


@login_required
@require_POST
def tier_toggle(request, tier_pk):
    tier = get_object_or_404(MembershipTier.objects.select_related("monetization_account__channel"), pk=tier_pk, monetization_account__channel__owner=request.user)
    tier.is_active = not tier.is_active
    tier.save(update_fields=["is_active", "updated_at"])
    return redirect("monetization:creator_dashboard", pk=tier.monetization_account.channel_id)


@login_required
@require_POST
def send_sandbox_tip(request, pk):
    channel = get_object_or_404(Channel, pk=pk)
    if channel.owner_id == request.user.pk:
        return HttpResponseForbidden("Channel owners cannot tip their own channel.")
    account = get_object_or_404(CreatorMonetizationAccount, channel=channel)
    if not account.is_ready_to_earn:
        return HttpResponseForbidden("This channel is not currently accepting tips.")
    form = TipForm(request.POST)
    if not form.is_valid():
        return render(request, "monetization/tip_form.html", {"channel": channel, "form": form, "stripe_enabled": stripe_gateway.stripe_enabled()}, status=400)
    _record_sandbox_payment(account=account, payer=request.user, kind=MonetizationTransaction.Kind.TIP, gross_amount_minor=form.amount_minor())
    return redirect("channel_detail", pk=channel.pk)


@login_required
@require_POST
def start_stripe_tip(request, pk):
    if not stripe_gateway.stripe_enabled():
        return HttpResponseForbidden("Stripe test mode is not enabled.")
    channel = get_object_or_404(Channel, pk=pk)
    if channel.owner_id == request.user.pk:
        return HttpResponseForbidden("Channel owners cannot tip their own channel.")
    account = get_object_or_404(CreatorMonetizationAccount, channel=channel, provider="stripe")
    if not account.is_ready_to_earn:
        return HttpResponseForbidden("This channel is not currently accepting tips.")
    form = TipForm(request.POST)
    if not form.is_valid():
        return render(request, "monetization/tip_form.html", {"channel": channel, "form": form, "stripe_enabled": True}, status=400)
    checkout = stripe_gateway.create_tip_checkout(
        connected_account_id=account.provider_account_id,
        amount_minor=form.amount_minor(),
        channel_name=channel.name,
        payer_id=request.user.pk,
        channel_id=channel.pk,
        success_url=_absolute(request, "channel_detail", channel.pk),
        cancel_url=_absolute(request, "monetization:tip_form", channel.pk),
    )
    return redirect(checkout.url)


@login_required
def tip_form(request, pk):
    channel = get_object_or_404(Channel, pk=pk)
    if channel.owner_id == request.user.pk:
        return HttpResponseForbidden("Channel owners cannot tip their own channel.")
    account = get_object_or_404(CreatorMonetizationAccount, channel=channel)
    if not account.is_ready_to_earn:
        return HttpResponseForbidden("This channel is not currently accepting tips.")
    return render(request, "monetization/tip_form.html", {"channel": channel, "form": TipForm(), "stripe_enabled": stripe_gateway.stripe_enabled() and account.provider == "stripe"})


@login_required
@require_POST
def join_sandbox_membership(request, tier_pk):
    tier = get_object_or_404(MembershipTier.objects.select_related("monetization_account", "monetization_account__channel"), pk=tier_pk, is_active=True)
    account = tier.monetization_account
    channel = account.channel
    if channel.owner_id == request.user.pk:
        return HttpResponseForbidden("Channel owners cannot join their own membership.")
    if not account.is_ready_to_earn:
        return HttpResponseForbidden("This channel is not currently accepting memberships.")
    existing_active = ChannelMembershipSubscription.objects.filter(subscriber=request.user, status=ChannelMembershipSubscription.Status.ACTIVE, tier__monetization_account=account).select_related("tier").first()
    if existing_active and existing_active.tier_id == tier.pk:
        return redirect("channel_detail", pk=channel.pk)
    if existing_active:
        existing_active.status = ChannelMembershipSubscription.Status.ENDED
        existing_active.ended_at = timezone.now()
        existing_active.save(update_fields=["status", "ended_at"])
    subscription, unused = ChannelMembershipSubscription.objects.get_or_create(tier=tier, subscriber=request.user, defaults={"status": ChannelMembershipSubscription.Status.ACTIVE})
    subscription.status = ChannelMembershipSubscription.Status.ACTIVE
    subscription.canceled_at = None
    subscription.ended_at = None
    if not subscription.provider_subscription_id:
        subscription.provider_subscription_id = f"test_sub_{subscription.pk}"
    subscription.save()
    _record_sandbox_payment(account=account, payer=request.user, membership_subscription=subscription, kind=MonetizationTransaction.Kind.MEMBERSHIP, gross_amount_minor=tier.price_minor, currency=tier.currency)
    return redirect("channel_detail", pk=channel.pk)


@login_required
@require_POST
def start_stripe_membership(request, tier_pk):
    if not stripe_gateway.stripe_enabled():
        return HttpResponseForbidden("Stripe test mode is not enabled.")
    tier = get_object_or_404(MembershipTier.objects.select_related("monetization_account__channel"), pk=tier_pk, is_active=True)
    account = tier.monetization_account
    channel = account.channel
    if channel.owner_id == request.user.pk:
        return HttpResponseForbidden("Channel owners cannot join their own membership.")
    if account.provider != "stripe" or not account.is_ready_to_earn:
        return HttpResponseForbidden("This channel is not currently accepting Stripe memberships.")
    existing_active = ChannelMembershipSubscription.objects.filter(
        subscriber=request.user,
        status=ChannelMembershipSubscription.Status.ACTIVE,
        tier__monetization_account=account,
    ).first()
    if existing_active:
        if existing_active.tier_id == tier.pk:
            return redirect("channel_detail", pk=channel.pk)
        return HttpResponseBadRequest(
            "Cancel your existing channel membership before choosing another tier."
        )
    checkout = stripe_gateway.create_membership_checkout(
        connected_account_id=account.provider_account_id,
        tier_id=tier.pk,
        tier_name=f"{channel.name} · {tier.name}",
        price_minor=tier.price_minor,
        channel_id=channel.pk,
        payer_id=request.user.pk,
        success_url=_absolute(request, "channel_detail", channel.pk),
        cancel_url=_absolute(request, "channel_detail", channel.pk),
    )
    return redirect(checkout.url)


@login_required
@require_POST
def cancel_sandbox_membership(request, subscription_pk):
    subscription = get_object_or_404(ChannelMembershipSubscription.objects.select_related("tier__monetization_account__channel"), pk=subscription_pk, subscriber=request.user, status=ChannelMembershipSubscription.Status.ACTIVE)
    subscription.status = ChannelMembershipSubscription.Status.CANCELED
    subscription.canceled_at = timezone.now()
    subscription.ended_at = timezone.now()
    subscription.save(update_fields=["status", "canceled_at", "ended_at"])
    return redirect("channel_detail", pk=subscription.tier.monetization_account.channel_id)


@login_required
@require_POST
def cancel_stripe_membership(request, subscription_pk):
    subscription = get_object_or_404(ChannelMembershipSubscription.objects.select_related("tier__monetization_account__channel"), pk=subscription_pk, subscriber=request.user, status=ChannelMembershipSubscription.Status.ACTIVE)
    if not subscription.provider_subscription_id or subscription.provider_subscription_id.startswith("test_sub_"):
        return HttpResponseBadRequest("This is not a Stripe subscription.")
    stripe_gateway.cancel_membership_at_period_end(subscription.provider_subscription_id)
    subscription.canceled_at = timezone.now()
    subscription.save(update_fields=["canceled_at"])
    return redirect("channel_detail", pk=subscription.tier.monetization_account.channel_id)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not stripe_gateway.stripe_enabled():
        return HttpResponse(status=404)
    signature = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe_gateway.construct_webhook_event(request.body, signature)
    except Exception:
        return HttpResponseBadRequest("Invalid Stripe webhook.")

    event_id = _field(event, "id", "")
    event_type = _field(event, "type", "")
    data = _field(event, "data", {})
    obj = _field(data, "object", {})

    if event_type == "checkout.session.completed":
        metadata = _meta(obj)
        kind = metadata.get("ytclone_kind")
        payer_id = metadata.get("ytclone_payer_id")
        payer = get_user_model().objects.filter(pk=payer_id).first()
        if kind == "tip":
            channel = Channel.objects.filter(pk=metadata.get("ytclone_channel_id")).first()
            if channel and payer:
                account = CreatorMonetizationAccount.objects.filter(channel=channel, provider="stripe").first()
                gross = int(metadata.get("ytclone_gross_minor", 0))
                fee = int(metadata.get("ytclone_platform_fee_minor", 0))
                if account and gross > 0:
                    MonetizationTransaction.objects.get_or_create(
                        provider_event_id=event_id,
                        defaults={
                            "monetization_account": account,
                            "payer": payer,
                            "kind": MonetizationTransaction.Kind.TIP,
                            "status": MonetizationTransaction.Status.SUCCEEDED,
                            "currency": (_field(obj, "currency", "usd") or "usd").upper(),
                            "gross_amount_minor": gross,
                            "platform_fee_minor": fee,
                            "creator_net_minor": gross - fee,
                            "platform_fee_bps": settings.MONETIZATION_PLATFORM_FEE_BPS,
                            "provider_payment_id": str(_field(obj, "payment_intent", "")),
                        },
                    )
        elif kind == "membership":
            tier = MembershipTier.objects.select_related("monetization_account").filter(pk=metadata.get("ytclone_tier_id")).first()
            provider_subscription_id = str(_field(obj, "subscription", "") or "")
            if tier and payer and provider_subscription_id:
                subscription, unused = ChannelMembershipSubscription.objects.get_or_create(tier=tier, subscriber=payer)
                subscription.status = ChannelMembershipSubscription.Status.ACTIVE
                subscription.provider_subscription_id = provider_subscription_id
                subscription.canceled_at = None
                subscription.ended_at = None
                subscription.save()
                fee = (tier.price_minor * settings.MONETIZATION_PLATFORM_FEE_BPS) // 10000
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
                        "platform_fee_bps": settings.MONETIZATION_PLATFORM_FEE_BPS,
                        "provider_payment_id": provider_subscription_id,
                    },
                )

    elif event_type in {"customer.subscription.updated", "customer.subscription.deleted"}:
        provider_subscription_id = str(_field(obj, "id", "") or "")
        subscription = ChannelMembershipSubscription.objects.filter(provider_subscription_id=provider_subscription_id).first()
        if subscription:
            stripe_status = str(_field(obj, "status", "") or "")
            if event_type == "customer.subscription.deleted" or stripe_status in {"canceled", "unpaid", "incomplete_expired"}:
                subscription.status = ChannelMembershipSubscription.Status.ENDED
                subscription.ended_at = timezone.now()
            elif stripe_status == "past_due":
                subscription.status = ChannelMembershipSubscription.Status.PAST_DUE
            elif stripe_status in {"active", "trialing"}:
                subscription.status = ChannelMembershipSubscription.Status.ACTIVE
            subscription.save(update_fields=["status", "ended_at"])

    return HttpResponse(status=200)
