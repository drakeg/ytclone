from dataclasses import dataclass

from django.db.models import QuerySet

from video.models import Channel, Video
from video.services.channel_access import available_channels


SUBSCRIPTIONS_FEED_LIMIT = 24


@dataclass(frozen=True)
class SubscriptionsFeed:
    channels: QuerySet
    videos: QuerySet
    selected_channel: Channel | None = None


def get_subscriptions_feed(user, channel=None, limit=None):
    channels = (
        available_channels(user)
        .filter(subscribers=user)
        .select_related("owner")
        .order_by("name", "pk")
    )

    selected_channel = None
    try:
        channel_id = int(channel) if channel is not None else None
    except (TypeError, ValueError):
        channel_id = None
    if channel_id and channel_id > 0:
        selected_channel = channels.filter(pk=channel_id).first()

    videos = (
        Video.objects.visible_to(user)
        .filter(channel__in=channels, short_metadata__isnull=True)
        .select_related("author", "category", "channel")
        .prefetch_related("hashtags")
        .order_by("-pub_date", "-pk")
    )
    if selected_channel is not None:
        videos = videos.filter(channel=selected_channel)
    if limit is not None:
        videos = videos[: max(0, int(limit))]

    return SubscriptionsFeed(
        channels=channels,
        videos=videos,
        selected_channel=selected_channel,
    )
