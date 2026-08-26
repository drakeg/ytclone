from django import template

from monetization.models import ChannelMembershipSubscription

register = template.Library()


@register.simple_tag
def supporter_badge_for(user, video):
    if not getattr(user, "is_authenticated", False) or not video.channel_id:
        return False
    return ChannelMembershipSubscription.objects.filter(
        subscriber=user,
        status=ChannelMembershipSubscription.Status.ACTIVE,
        show_supporter_badge=True,
        tier__monetization_account__channel_id=video.channel_id,
    ).exists()
