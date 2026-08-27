from django.db.models import Count, Q
from django.shortcuts import render

from .models import Video
from .services.channel_access import available_channels, require_available_channel


def channel_list(request):
    channels = (
        available_channels(request.user)
        .select_related("owner")
        .annotate(
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
        )
        .order_by("-subscriber_count", "name", "pk")
    )
    return render(request, "videos/channel_list.html", {"channels": channels})


def channel_detail(request, pk):
    channel = require_available_channel(request.user, pk=pk)
    visible = channel.videos.visible_to(request.user).select_related("author", "category")
    videos = visible.filter(short_metadata__isnull=True)
    shorts = visible.filter(short_metadata__isnull=False)
    return render(
        request,
        "videos/channel_detail.html",
        {"channel": channel, "videos": videos, "shorts": shorts},
    )


def channel_community(request, pk):
    require_available_channel(request.user, pk=pk)
    from video.community_views import channel_community as community_view
    return community_view(request, pk)
