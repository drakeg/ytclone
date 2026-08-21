from dataclasses import dataclass

from django.db.models import Count, QuerySet, Sum
from django.db.models.functions import Coalesce

from video.models import Channel, Video
from video.services.watch_time import watch_metrics_for_videos


@dataclass(frozen=True)
class CreatorAnalytics:
    video_count: int
    total_views: int
    total_likes: int
    total_dislikes: int
    subscriber_count: int
    videos: QuerySet
    total_watch_seconds: int = 0
    total_watch_hours_display: str = "0.0"
    range_days: int | None = None


@dataclass(frozen=True)
class ChannelAnalytics:
    channel: Channel
    video_count: int
    total_views: int
    total_likes: int
    total_dislikes: int
    subscriber_count: int
    videos: QuerySet


def get_creator_analytics(user, days=None):
    creator_videos = Video.objects.filter(author=user, deleted_at__isnull=True)
    video_totals = creator_videos.aggregate(
        video_count=Count("id"),
        total_views=Coalesce(Sum("views"), 0),
    )
    subscriber_count = (
        Channel.objects.filter(owner=user)
        .values("subscribers")
        .exclude(subscribers=None)
        .distinct()
        .count()
    )
    videos = list(
        creator_videos.select_related("category")
        .annotate(
            like_count=Count("likes", distinct=True),
            dislike_count=Count("dislikes", distinct=True),
        )
        .order_by("-views", "-like_count", "-pub_date", "-pk")
    )
    watch_metrics = watch_metrics_for_videos(videos, days=days)
    for video in videos:
        metrics = watch_metrics[video.pk]
        for name, value in metrics.items():
            setattr(video, name, value)

    return CreatorAnalytics(
        video_count=video_totals["video_count"],
        total_views=video_totals["total_views"],
        total_likes=Video.likes.through.objects.filter(
            video__author=user, video__deleted_at__isnull=True
        ).count(),
        total_dislikes=Video.dislikes.through.objects.filter(
            video__author=user, video__deleted_at__isnull=True
        ).count(),
        subscriber_count=subscriber_count,
        videos=videos,
        total_watch_seconds=sum(video.watch_seconds for video in videos),
        total_watch_hours_display=f"{sum(video.watch_seconds for video in videos) / 3600:.1f}",
        range_days=days,
    )


def get_channel_analytics(channel):
    channel_videos = Video.objects.filter(channel=channel, deleted_at__isnull=True)
    totals = channel_videos.aggregate(
        video_count=Count("id"),
        total_views=Coalesce(Sum("views"), 0),
    )
    videos = (
        channel_videos.select_related("category")
        .annotate(
            like_count=Count("likes", distinct=True),
            dislike_count=Count("dislikes", distinct=True),
        )
        .order_by("-views", "-like_count", "-pub_date", "-pk")
    )
    return ChannelAnalytics(
        channel=channel,
        video_count=totals["video_count"],
        total_views=totals["total_views"],
        total_likes=Video.likes.through.objects.filter(
            video__channel=channel, video__deleted_at__isnull=True
        ).count(),
        total_dislikes=Video.dislikes.through.objects.filter(
            video__channel=channel, video__deleted_at__isnull=True
        ).count(),
        subscriber_count=channel.subscribers.count(),
        videos=videos,
    )
