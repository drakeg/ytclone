from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

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
        membership.is_stripe_membership = bool(
            provider_id and not provider_id.startswith("test_sub_")
        )
    return render(
        request,
        "monetization/membership_billing.html",
        {"memberships": memberships},
    )


@login_required
@require_POST
def toggle_supporter_badge(request, subscription_pk):
    membership = get_object_or_404(
        ChannelMembershipSubscription,
        pk=subscription_pk,
        subscriber=request.user,
        status=ChannelMembershipSubscription.Status.ACTIVE,
    )
    membership.show_supporter_badge = not membership.show_supporter_badge
    membership.save(update_fields=["show_supporter_badge"])
    return redirect("monetization:membership_billing")
