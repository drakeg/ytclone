import math

from django.db import transaction
from django.db.models import Max

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
    bookmark, created = VideoBookmark.objects.update_or_create(
        user=user,
        video=video,
        position_seconds=position_seconds,
        defaults={"label": cleaned_label},
    )
    if created:
        last_position = (
            VideoBookmark.objects.filter(user=user)
            .exclude(pk=bookmark.pk)
            .aggregate(max_position=Max("sort_position"))["max_position"]
        )
        bookmark.sort_position = (
            last_position + 1 if last_position is not None else 0
        )
        bookmark.save(update_fields=["sort_position"])
    return bookmark


def get_visible_bookmarks(user):
    return user.video_bookmarks.filter(
        video__in=Video.objects.visible_to(user)
    ).select_related("video", "video__author").order_by("-updated_at", "-pk")


@transaction.atomic
def move_bookmark(*, user, bookmark, direction):
    if bookmark.user_id != getattr(user, "pk", None):
        return False
    if direction not in {"up", "down"}:
        return False

    ordered = list(
        VideoBookmark.objects.select_for_update()
        .filter(user=user)
        .order_by("sort_position", "-updated_at", "-pk")
    )
    visible_ids = set(
        Video.objects.visible_to(user)
        .filter(pk__in=[item.video_id for item in ordered])
        .values_list("pk", flat=True)
    )
    visible_slots = [
        index
        for index, item in enumerate(ordered)
        if item.video_id in visible_ids
    ]
    current_visible_index = next(
        (
            index
            for index, slot in enumerate(visible_slots)
            if ordered[slot].pk == bookmark.pk
        ),
        None,
    )
    if current_visible_index is None:
        return False

    target_visible_index = (
        current_visible_index - 1
        if direction == "up"
        else current_visible_index + 1
    )
    if target_visible_index < 0 or target_visible_index >= len(visible_slots):
        return False

    current_slot = visible_slots[current_visible_index]
    target_slot = visible_slots[target_visible_index]
    ordered[current_slot], ordered[target_slot] = (
        ordered[target_slot],
        ordered[current_slot],
    )
    for position, item in enumerate(ordered):
        item.sort_position = position
    VideoBookmark.objects.bulk_update(ordered, ["sort_position"])
    return True
