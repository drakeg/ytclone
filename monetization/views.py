import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from video.models import Channel

from .forms import MembershipTierForm
from .models import (
    ChannelMembershipSubscription,
    CreatorMonetizationAccount,
    MembershipTier,
    MonetizationTransaction,
)


def _owned_channel(user, pk):
    return get_object_or_404(Channel, pk=pk, owner=user)


@login_required
def creator_dashboard(request, pk):
    channel = _owned_channel(request.user, pk)
    account = CreatorMonetizationAccount.objects.filter(channel=channel).first()
    tiers = account.membership_tiers.order_by("price_minor", "name") if account else []
    transactions = (
        account.transactions.select_related("payer").all()[:20] if account else []
    )
    creator_net_minor = 0
    platform_fee_minor = 0
    if account:
        totals = account.transactions.filter(
            status=MonetizationTransaction.Status.SUCCEEDED
        ).aggregate(
            creator_net=Sum("creator_net_minor"),
            platform_fee=Sum("platform_fee_minor"),
        )
        creator_net_minor = totals["creator_net"] or 0
        platform_fee_minor = totals["platform_fee"] or 0

    return render(
        request,
        "monetization/creator_dashboard.html",
        {
            "channel": channel,
            "account": account,
            "tiers": tiers,
            "transactions": transactions,
            "creator_net_minor": creator_net_minor,
            "platform_fee_minor": platform_fee_minor,
            "platform_fee_bps": settings.MONETIZATION_PLATFORM_FEE_BPS,
        },
    )


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
def tier_create(request, pk):
    channel = _owned_channel(request.user, pk)
    account = get_object_or_404(CreatorMonetizationAccount, channel=channel)
    if not account.is_ready_to_earn:
        return HttpResponseForbidden("Enable channel monetization before creating tiers.")

    if request.method == "POST":
        form = MembershipTierForm(request.POST)
        if form.is_valid():
            MembershipTier.objects.create(
                monetization_account=account,
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
                price_minor=form.price_minor(),
                currency="USD",
            )
            return redirect("monetization:creator_dashboard", pk=channel.pk)
    else:
        form = MembershipTierForm()

    return render(
        request,
        "monetization/tier_form.html",
        {"channel": channel, "form": form},
    )


@login_required
@require_POST
def join_sandbox_membership(request, tier_pk):
    tier = get_object_or_404(
        MembershipTier.objects.select_related(
            "monetization_account", "monetization_account__channel"
        ),
        pk=tier_pk,
        is_active=True,
    )
    account = tier.monetization_account
    channel = account.channel
    if channel.owner_id == request.user.pk:
        return HttpResponseForbidden("Channel owners cannot join their own membership.")
    if not account.is_ready_to_earn:
        return HttpResponseForbidden("This channel is not currently accepting memberships.")

    existing_active = ChannelMembershipSubscription.objects.filter(
        subscriber=request.user,
        status=ChannelMembershipSubscription.Status.ACTIVE,
        tier__monetization_account=account,
    ).select_related("tier").first()
    if existing_active and existing_active.tier_id == tier.pk:
        return redirect("channel_detail", pk=channel.pk)
    if existing_active:
        existing_active.status = ChannelMembershipSubscription.Status.ENDED
        existing_active.ended_at = timezone.now()
        existing_active.save(update_fields=["status", "ended_at"])

    subscription, unused = ChannelMembershipSubscription.objects.get_or_create(
        tier=tier,
        subscriber=request.user,
        defaults={"status": ChannelMembershipSubscription.Status.ACTIVE},
    )
    subscription.status = ChannelMembershipSubscription.Status.ACTIVE
    subscription.canceled_at = None
    subscription.ended_at = None
    if not subscription.provider_subscription_id:
        subscription.provider_subscription_id = f"test_sub_{subscription.pk}"
    subscription.save()

    fee_bps = settings.MONETIZATION_PLATFORM_FEE_BPS
    platform_fee_minor = (tier.price_minor * fee_bps) // 10000
    MonetizationTransaction.objects.create(
        monetization_account=account,
        payer=request.user,
        membership_subscription=subscription,
        kind=MonetizationTransaction.Kind.MEMBERSHIP,
        status=MonetizationTransaction.Status.SUCCEEDED,
        currency=tier.currency,
        gross_amount_minor=tier.price_minor,
        platform_fee_minor=platform_fee_minor,
        provider_fee_minor=0,
        creator_net_minor=tier.price_minor - platform_fee_minor,
        platform_fee_bps=fee_bps,
        idempotency_key=f"sandbox-membership-{uuid.uuid4()}",
        provider_payment_id=f"test_pay_{uuid.uuid4().hex}",
    )
    return redirect("channel_detail", pk=channel.pk)
