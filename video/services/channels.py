from django.db.models import Q

from video.models import Channel


def accessible_channels(user):
    if not getattr(user, "is_authenticated", False):
        return Channel.objects.none()
    return Channel.objects.filter(
        Q(owner=user) | Q(memberships__user=user)
    ).distinct()


def can_edit_video(user, video):
    return video.author_id == user.pk or (
        video.channel_id is not None
        and accessible_channels(user).filter(pk=video.channel_id).exists()
    )
