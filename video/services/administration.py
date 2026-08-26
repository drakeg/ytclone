from django.contrib.auth import get_user_model

from monetization.models import ChannelMembershipSubscription
from video.models import Channel, Comment, Video


User = get_user_model()


def get_site_admin_overview():
    return {
        "user_count": User.objects.count(),
        "channel_count": Channel.objects.count(),
        "video_count": Video.objects.filter(deleted_at__isnull=True).count(),
        "comment_count": Comment.objects.count(),
        "hidden_comment_count": Comment.objects.filter(is_hidden=True).count(),
        "active_paid_membership_count": ChannelMembershipSubscription.objects.filter(
            status=ChannelMembershipSubscription.Status.ACTIVE
        ).count(),
        "recent_comments": Comment.objects.select_related(
            "author", "video", "video__channel"
        ).order_by("-pub_date", "-pk")[:50],
    }


def moderate_site_comment(*, comment_id, action):
    if action not in {"hide", "restore"}:
        raise ValueError("Invalid moderation action.")
    comment = Comment.objects.filter(pk=comment_id).first()
    if comment is None:
        return False
    comment.is_hidden = action == "hide"
    comment.save(update_fields=["is_hidden"])
    return True


def get_creator_audience(user):
    channels = Channel.objects.filter(owner=user).order_by("name", "pk")
    result = []
    for channel in channels:
        free_subscribers = channel.subscribers.order_by("username")
        paid_memberships = (
            ChannelMembershipSubscription.objects.filter(
                tier__monetization_account__channel=channel
            )
            .select_related("subscriber", "tier")
            .order_by("-started_at", "-pk")
        )
        result.append(
            {
                "channel": channel,
                "free_subscribers": free_subscribers,
                "paid_memberships": paid_memberships,
            }
        )
    return result
