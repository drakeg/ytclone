from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import ChannelMembershipSubscription


@login_required
def membership_billing(request):
    memberships = list(
        ChannelMembershipSubscription.objects.filter(subscriber=request.user)
        .select_related("tier", "tier__monetization_account", "tier__monetization_account__channel")
        .order_by("-started_at")
    )
    for membership in memberships:
        provider_id = membership.provider_subscription_id or ""
        membership.is_stripe_membership = bool(provider_id and not provider_id.startswith("test_sub_"))
    return render(
        request,
        "monetization/membership_billing.html",
        {"memberships": memberships},
    )
