from monetization.models import ChannelMembershipSubscription

from ..community_models import CommunityPost


def has_active_channel_membership(user, channel):
    if not getattr(user, "is_authenticated", False):
        return False
    if channel.owner_id == user.pk:
        return True
    return ChannelMembershipSubscription.objects.filter(
        subscriber=user,
        status=ChannelMembershipSubscription.Status.ACTIVE,
        tier__monetization_account__channel=channel,
    ).exists()


def can_view_community_post(user, post):
    if hasattr(post, "moderation_state") and post.channel.owner_id != getattr(user, "pk", None):
        return False
    if post.audience == CommunityPost.Audience.EVERYONE:
        return True
    return has_active_channel_membership(user, post.channel)


def visible_community_posts(user, channel):
    posts = CommunityPost.objects.filter(channel=channel)
    if channel.owner_id != getattr(user, "pk", None):
        posts = posts.filter(moderation_state__isnull=True)
    if channel.owner_id == getattr(user, "pk", None):
        return posts
    if has_active_channel_membership(user, channel):
        return posts
    return posts.filter(audience=CommunityPost.Audience.EVERYONE)


def supporter_badge_user_ids(channel):
    return set(
        ChannelMembershipSubscription.objects.filter(
            tier__monetization_account__channel=channel,
            status=ChannelMembershipSubscription.Status.ACTIVE,
            show_supporter_badge=True,
        ).values_list("subscriber_id", flat=True)
    )
