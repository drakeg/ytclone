from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from .services.channel_access import require_available_channel
from .services.notifications import notify_subscription


@login_required
@require_POST
def subscribe(request, pk):
    channel = require_available_channel(request.user, pk=pk)
    if channel.owner_id == request.user.pk:
        return HttpResponseForbidden("You cannot subscribe to your own channel.")
    if channel.subscribers.filter(pk=request.user.pk).exists():
        channel.subscribers.remove(request.user)
    else:
        channel.subscribers.add(request.user)
        notify_subscription(channel=channel, actor=request.user)
    return redirect("channel_detail", pk=channel.pk)
