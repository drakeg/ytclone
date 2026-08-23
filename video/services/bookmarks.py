import math

from django.db import transaction

from ..models import Video, VideoBookmark


MAX_BOOKMARK_SECONDS = 24 * 60 * 60
MAX_BOOKMARK_LABEL_LENGTH = 120


class BookmarkValidationError(ValueError):
    pass


def _clean_position(value):
    try:
        position = float(value)
    except (TypeError, ValueError):
        raise BookmarkValidationError("Enter a valid playback position.") from None
    if not math.isfinite(position):
        raise BookmarkValidationError("Enter a valid playback position.")
    position = round(position)
    if position < 0 or position > MAX_BOOKMARK_SECONDS:
        raise BookmarkValidationError("Playback position must be between 0 and 24 hours.")
    return position


def _clean_label(value):
    label = str(value or "").strip()
    if not label:
        raise BookmarkValidationError("Enter a bookmark label.")
    if len(label) > MAX_BOOKMARK_LABEL_LENGTH:
        raise BookmarkValidationError("Bookmark labels are limited to 120 characters.")
    return label


@transaction.atomic
def save_bookmark(*, user, video, position, label):
    position_seconds = _clean_position(position)
    cleaned_label = _clean_label(label)
    bookmark, unused = VideoBookmark.objects.update_or_create(
        user=user,
        video=video,
        position_seconds=position_seconds,
        defaults={"label": cleaned_label},
    )
    return bookmark


def get_visible_bookmarks(user):
    return user.video_bookmarks.filter(
        video__in=Video.objects.visible_to(user)
    ).select_related("video", "video__author").order_by("-updated_at", "-pk")
