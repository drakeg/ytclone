from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services.subscriptions import get_subscriptions_feed


@login_required
def subscriptions_feed(request):
    feed = get_subscriptions_feed(request.user)
    return render(
        request,
        "videos/subscriptions_feed.html",
        {"subscribed_channels": feed.channels, "videos": feed.videos},
    )
