from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import SubscriptionNotificationPreference
from .services.channel_access import require_available_channel
from .services.notifications import notify_subscription


def _safe_next(request, channel):
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return None


@login_required
@require_POST
def subscribe(request, pk):
    channel = require_available_channel(request.user, pk=pk)
    if channel.owner_id == request.user.pk:
        return HttpResponseForbidden("You cannot subscribe to your own channel.")
    if channel.subscribers.filter(pk=request.user.pk).exists():
        channel.subscribers.remove(request.user)
        SubscriptionNotificationPreference.objects.filter(user=request.user, channel=channel).delete()
        subscribed = False
    else:
        channel.subscribers.add(request.user)
        notify_subscription(channel=channel, actor=request.user)
        subscribed = True

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "subscribed": subscribed,
                "subscriber_count": channel.subscribers.count(),
            }
        )

    next_url = _safe_next(request, channel)
    if next_url:
        return redirect(next_url)
    return redirect("channel_detail", pk=channel.pk)


@login_required
@require_POST
def upload_notifications(request, pk):
    channel = require_available_channel(request.user, pk=pk)
    if channel.owner_id == request.user.pk:
        return HttpResponseForbidden("You cannot manage subscription notifications for your own channel.")
    if not channel.subscribers.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Subscribe to this channel before changing upload notifications.")

    enabled = request.POST.get("enabled") == "1"
    preference, _ = SubscriptionNotificationPreference.objects.update_or_create(
        user=request.user,
        channel=channel,
        defaults={"upload_notifications_enabled": enabled},
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"upload_notifications_enabled": preference.upload_notifications_enabled})

    next_url = _safe_next(request, channel)
    if next_url:
        return redirect(next_url)
    return redirect("channel_detail", pk=channel.pk)
