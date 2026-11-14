from django.core.paginator import Paginator
from django.shortcuts import render

from .models import SubscriptionNotificationPreference
from .services.channel_access import get_channel_directory, require_available_channel


CHANNEL_VIDEO_PAGE_SIZE = 12
CHANNEL_SHORT_PAGE_SIZE = 8
CHANNEL_DIRECTORY_PAGE_SIZE = 24


def channel_list(request):
    channels, selected_query = get_channel_directory(
        request.user,
        request.GET.get("q", ""),
    )
    channels_page = Paginator(channels, CHANNEL_DIRECTORY_PAGE_SIZE).get_page(
        request.GET.get("page")
    )
    return render(
        request,
        "videos/channel_list.html",
        {
            "channels": channels_page,
            "channels_page": channels_page,
            "channel_query": selected_query,
        },
    )


def channel_detail(request, pk):
    channel = require_available_channel(request.user, pk=pk)
    visible = channel.videos.visible_to(request.user).select_related("author", "category")
    videos = Paginator(
        visible.filter(short_metadata__isnull=True).order_by("-pub_date", "-pk"),
        CHANNEL_VIDEO_PAGE_SIZE,
    ).get_page(request.GET.get("video_page"))
    shorts = Paginator(
        visible.filter(short_metadata__isnull=False).order_by("-pub_date", "-pk"),
        CHANNEL_SHORT_PAGE_SIZE,
    ).get_page(request.GET.get("short_page"))

    is_subscribed = False
    upload_notifications_enabled = True
    if request.user.is_authenticated and request.user.pk != channel.owner_id:
        is_subscribed = channel.subscribers.filter(pk=request.user.pk).exists()
        if is_subscribed:
            preference = SubscriptionNotificationPreference.objects.filter(
                user=request.user,
                channel=channel,
            ).first()
            if preference is not None:
                upload_notifications_enabled = preference.upload_notifications_enabled

    return render(
        request,
        "videos/channel_detail.html",
        {
            "channel": channel,
            "videos": videos,
            "shorts": shorts,
            "is_subscribed": is_subscribed,
            "upload_notifications_enabled": upload_notifications_enabled,
        },
    )


def channel_community(request, pk):
    require_available_channel(request.user, pk=pk)
    from video.community_views import channel_community as community_view
    return community_view(request, pk)
