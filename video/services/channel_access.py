from django.db.models import Count, Q
from django.http import Http404

from video.models import Channel, Video


def is_channel_suspended(channel):
    return hasattr(channel, "moderation_state")


def can_inspect_suspended_channels(user):
    return bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "is_staff", False)
    )


def available_channels(user):
    channels = Channel.objects.all()
    if can_inspect_suspended_channels(user):
        return channels
    return channels.filter(moderation_state__isnull=True)


def require_available_channel(user, *, pk):
    try:
        return available_channels(user).get(pk=pk)
    except Channel.DoesNotExist:
        raise Http404("Channel not found") from None


CHANNEL_DIRECTORY_QUERY_MAX_LENGTH = 120


def get_channel_directory(user, requested_query=""):
    selected_query = str(requested_query or "").strip()[:CHANNEL_DIRECTORY_QUERY_MAX_LENGTH]
    channels = available_channels(user).select_related("owner")
    if selected_query:
        channels = channels.filter(
            Q(name__icontains=selected_query)
            | Q(description__icontains=selected_query)
            | Q(owner__username__icontains=selected_query)
        )
    channels = channels.annotate(
        subscriber_count=Count("subscribers", distinct=True),
        public_video_count=Count(
            "videos",
            filter=Q(
                videos__deleted_at__isnull=True,
                videos__publication_status=Video.PublicationStatus.PUBLISHED,
                videos__audience=Video.Audience.EVERYONE,
            ),
            distinct=True,
        ),
    ).order_by("-subscriber_count", "name", "pk")
    return channels, selected_query
