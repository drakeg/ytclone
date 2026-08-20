from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from video.models import Channel

from . import stripe_gateway
from .models import CreatorMonetizationAccount


@login_required
def onboarding_refresh(request, pk):
    """Create a fresh single-use Account Link when Stripe asks for a refresh."""
    if not stripe_gateway.stripe_enabled():
        return HttpResponseForbidden("Stripe test mode is not enabled.")

    channel = get_object_or_404(Channel, pk=pk, owner=request.user)
    account = get_object_or_404(
        CreatorMonetizationAccount,
        channel=channel,
        provider="stripe",
    )
    refresh_url = request.build_absolute_uri(
        reverse("monetization:stripe_onboarding_refresh", args=[channel.pk])
    )
    return_url = request.build_absolute_uri(
        reverse("monetization:stripe_onboarding_return", args=[channel.pk])
    )
    link = stripe_gateway.create_account_onboarding_link(
        account_id=account.provider_account_id,
        refresh_url=refresh_url,
        return_url=return_url,
    )
    return redirect(link)
