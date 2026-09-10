from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from .services.subscriptions import SUBSCRIPTIONS_FEED_LIMIT, get_subscriptions_feed


@login_required
def subscriptions_feed(request):
    feed = get_subscriptions_feed(request.user, channel=request.GET.get("channel"))
    videos = Paginator(feed.videos, SUBSCRIPTIONS_FEED_LIMIT).get_page(request.GET.get("page"))
    return render(
        request,
        "videos/subscriptions_feed.html",
        {
            "subscribed_channels": feed.channels,
            "videos": videos,
            "selected_channel": feed.selected_channel,
        },
    )
