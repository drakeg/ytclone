from django.db import transaction
from django.db.models import F, Max

from ..models import Playlist, PlaylistItem, Video


WATCH_LATER_NAME = "Watch Later"
WATCH_LATER_SORTS = {
    "newest": ("-playlist_items__added_at", "-playlist_items__pk"),
    "oldest": ("playlist_items__added_at", "playlist_items__pk"),
    "title": ("title", "-playlist_items__added_at", "-playlist_items__pk"),
    "manual": ("playlist_items__position", "playlist_items__added_at", "playlist_items__pk"),
}


def get_watch_later_playlist(user, *, create=False):
    if not user.is_authenticated:
        return None

    if create:
        playlist, _ = Playlist.objects.get_or_create(
            owner=user,
            name=WATCH_LATER_NAME,
            defaults={
                "description": "Videos saved to watch later.",
                "visibility": Playlist.Visibility.PRIVATE,
            },
        )
        if playlist.visibility != Playlist.Visibility.PRIVATE:
            playlist.visibility = Playlist.Visibility.PRIVATE
            playlist.save(update_fields=["visibility", "updated_at"])
        return playlist

    return Playlist.objects.filter(owner=user, name=WATCH_LATER_NAME).first()


def is_saved_for_later(user, video):
    playlist = get_watch_later_playlist(user)
    if playlist is None:
        return False
    return PlaylistItem.objects.filter(playlist=playlist, video=video).exists()


def save_for_later(user, video):
    playlist = get_watch_later_playlist(user, create=True)
    existing = PlaylistItem.objects.filter(playlist=playlist, video=video).first()
    if existing is not None:
        return existing, False

    last_position = playlist.items.aggregate(max_position=Max("position"))["max_position"]
    item = PlaylistItem.objects.create(
        playlist=playlist,
        video=video,
        position=(last_position + 1) if last_position is not None else 0,
    )
    return item, True


def remove_from_watch_later(user, video):
    playlist = get_watch_later_playlist(user)
    if playlist is None:
        return False
    deleted, _ = PlaylistItem.objects.filter(playlist=playlist, video=video).delete()
    return bool(deleted)


def watch_later_videos(user, query="", sort="newest"):
    playlist = get_watch_later_playlist(user)
    if playlist is None:
        return Video.objects.none()

    normalized_sort = sort if sort in WATCH_LATER_SORTS else "newest"
    videos = (
        Video.objects.visible_to(user)
        .filter(playlist_items__playlist=playlist)
        .select_related("author", "category", "channel")
        .prefetch_related("hashtags")
    )
    normalized_query = query.strip()
    if normalized_query:
        videos = videos.filter(title__icontains=normalized_query)
    return videos.order_by(*WATCH_LATER_SORTS[normalized_sort])


def completed_watch_later_video_ids(user):
    playlist = get_watch_later_playlist(user)
    if playlist is None:
        return Video.objects.none().values_list("pk", flat=True)

    completed_history = user.watch_history.filter(
        duration_seconds__gt=0,
        playback_position_seconds__gt=0,
    ).annotate(
        remaining_seconds=F("duration_seconds") - F("playback_position_seconds")
    ).filter(
        remaining_seconds__lte=5
    )

    return (
        Video.objects.visible_to(user)
        .filter(
            playlist_items__playlist=playlist,
            history_entries__in=completed_history,
        )
        .values_list("pk", flat=True)
        .distinct()
    )


@transaction.atomic
def move_watch_later_video(user, playlist, item, direction):
    """Move among visible Watch Later entries without exposing hidden entries."""
    if playlist.owner_id != user.pk or item.playlist_id != playlist.pk:
        return False
    if direction not in {"up", "down"}:
        return False

    ordered = list(
        PlaylistItem.objects.select_for_update()
        .filter(playlist=playlist)
        .order_by("position", "added_at", "pk")
    )
    visible_ids = set(
        Video.objects.visible_to(user)
        .filter(pk__in=[entry.video_id for entry in ordered])
        .values_list("pk", flat=True)
    )
    visible_indices = [
        index for index, entry in enumerate(ordered)
        if entry.video_id in visible_ids
    ]
    position = next(
        (index for index, slot in enumerate(visible_indices)
         if ordered[slot].pk == item.pk),
        None,
    )
    if position is None:
        return False
    target = position - 1 if direction == "up" else position + 1
    if target < 0 or target >= len(visible_indices):
        return False
    current_slot, target_slot = visible_indices[position], visible_indices[target]
    ordered[current_slot], ordered[target_slot] = ordered[target_slot], ordered[current_slot]
    for index, entry in enumerate(ordered):
        entry.position = index
    PlaylistItem.objects.bulk_update(ordered, ["position"])
    return True
