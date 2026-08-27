from django.http import Http404

from video.models import Channel


def is_channel_suspended(channel):
    return hasattr(channel, "moderation_state")


def can_inspect_suspended_channels(user):
    return bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "is_staff", False)
    )


def available_channels(user):
    channels = Channel.objects.all()
    if can_inspect_suspended_channels(user):
        return channels
    return channels.filter(moderation_state__isnull=True)


def require_available_channel(user, *, pk):
    try:
        return available_channels(user).get(pk=pk)
    except Channel.DoesNotExist:
        raise Http404("Channel not found") from None
