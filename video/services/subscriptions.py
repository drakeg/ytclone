from dataclasses import dataclass

from django.db.models import QuerySet

from video.models import Channel, Video
from video.services.channel_access import available_channels


SUBSCRIPTIONS_FEED_LIMIT = 24


@dataclass(frozen=True)
class SubscriptionsFeed:
    channels: QuerySet
    videos: QuerySet


def get_subscriptions_feed(user, limit=SUBSCRIPTIONS_FEED_LIMIT):
    channels = (
        available_channels(user)
        .filter(subscribers=user)
        .select_related("owner")
        .order_by("name", "pk")
    )
    videos = (
        Video.objects.visible_to(user)
        .filter(channel__in=channels, short_metadata__isnull=True)
        .select_related("author", "category", "channel")
        .prefetch_related("hashtags")
        .order_by("-pub_date", "-pk")[:limit]
    )
    return SubscriptionsFeed(channels=channels, videos=videos)
