from django.contrib.auth import get_user_model

from monetization.models import ChannelMembershipSubscription
from video.community_models import CommunityPost, CommunityReply
from video.models import Channel, Comment, Video
from video.moderation_models import ModerationAuditEvent
from video.services.moderation_actions import set_comment_hidden

User = get_user_model()


def get_site_admin_overview():
    return {
        "user_count": User.objects.count(), "channel_count": Channel.objects.count(), "video_count": Video.objects.filter(deleted_at__isnull=True).count(),
        "comment_count": Comment.objects.count(), "hidden_comment_count": Comment.objects.filter(is_hidden=True).count(),
        "active_paid_membership_count": ChannelMembershipSubscription.objects.filter(status=ChannelMembershipSubscription.Status.ACTIVE).count(),
        "recent_channels": Channel.objects.select_related("owner").order_by("name", "pk")[:50],
        "recent_comments": Comment.objects.select_related("author", "video", "video__channel").order_by("-pub_date", "-pk")[:25],
        "recent_videos": Video.objects.filter(deleted_at__isnull=True).select_related("author", "channel").order_by("-pub_date", "-pk")[:25],
        "recent_users": User.objects.order_by("-date_joined", "-pk")[:25],
        "recent_community_posts": CommunityPost.objects.select_related("author", "channel").order_by("-created_at", "-pk")[:25],
        "recent_community_replies": CommunityReply.objects.select_related("author", "post__channel").order_by("-created_at", "-pk")[:25],
        "recent_moderation_events": ModerationAuditEvent.objects.select_related("actor")[:50],
    }


def moderate_site_comment(*, actor, comment_id, action, reason):
    if action not in {"hide", "restore"}: raise ValueError("Invalid moderation action.")
    comment = Comment.objects.filter(pk=comment_id).first()
    if comment is None: return False
    set_comment_hidden(actor=actor, comment=comment, hidden=action == "hide", reason=reason); return True


def get_creator_audience(user):
    channels = Channel.objects.filter(owner=user).order_by("name", "pk"); result = []
    for channel in channels:
        free_subscribers = channel.subscribers.order_by("username")
        paid_memberships = ChannelMembershipSubscription.objects.filter(tier__monetization_account__channel=channel).select_related("subscriber", "tier").order_by("-started_at", "-pk")
        result.append({"channel": channel, "free_subscribers": free_subscribers, "paid_memberships": paid_memberships})
    return result
