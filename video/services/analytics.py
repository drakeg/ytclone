from dataclasses import dataclass

from django.db.models import Count, QuerySet, Sum
from django.db.models.functions import Coalesce

from video.models import Channel, Video


@dataclass(frozen=True)
class CreatorAnalytics:
    video_count: int
    total_views: int
    total_likes: int
    total_dislikes: int
    subscriber_count: int
    videos: QuerySet


@dataclass(frozen=True)
class ChannelAnalytics:
    channel: Channel
    video_count: int
    total_views: int
    total_likes: int
    total_dislikes: int
    subscriber_count: int
    videos: QuerySet


def get_creator_analytics(user):
    creator_videos = Video.objects.filter(author=user)
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
    videos = (
        creator_videos.select_related("category")
        .annotate(
            like_count=Count("likes", distinct=True),
            dislike_count=Count("dislikes", distinct=True),
        )
        .order_by("-views", "-like_count", "-pub_date", "-pk")
    )

    return CreatorAnalytics(
        video_count=video_totals["video_count"],
        total_views=video_totals["total_views"],
        total_likes=Video.likes.through.objects.filter(
            video__author=user
        ).count(),
        total_dislikes=Video.dislikes.through.objects.filter(
            video__author=user
        ).count(),
        subscriber_count=subscriber_count,
        videos=videos,
    )


def get_channel_analytics(channel):
    channel_videos = Video.objects.filter(channel=channel)
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
        total_likes=Video.likes.through.objects.filter(video__channel=channel).count(),
        total_dislikes=Video.dislikes.through.objects.filter(video__channel=channel).count(),
        subscriber_count=channel.subscribers.count(),
        videos=videos,
    )
