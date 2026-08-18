from django import template

from monetization.models import ChannelMembershipSubscription


register = template.Library()


@register.filter
def money_minor(value):
    try:
        return f"{int(value) / 100:.2f}"
    except (TypeError, ValueError):
        return "0.00"


@register.simple_tag
def paid_membership_for(user, channel):
    if not getattr(user, "is_authenticated", False):
        return None
    return (
        ChannelMembershipSubscription.objects.filter(
            subscriber=user,
            status=ChannelMembershipSubscription.Status.ACTIVE,
            tier__monetization_account__channel=channel,
        )
        .select_related("tier")
        .first()
    )
