from django.core.exceptions import PermissionDenied
from django.db import transaction

from ..models import PlaylistItem


@transaction.atomic
def move_playlist_item(*, playlist, item, user, direction):
    if playlist.owner_id != getattr(user, "pk", None):
        raise PermissionDenied("Only the playlist owner can reorder videos.")
    if item.playlist_id != playlist.pk:
        raise PermissionDenied("Playlist item does not belong to this playlist.")
    if direction not in {"up", "down"}:
        raise ValueError("Direction must be 'up' or 'down'.")

    ordered_items = list(
        PlaylistItem.objects.select_for_update()
        .filter(playlist=playlist)
        .order_by("position", "added_at", "pk")
    )
    current_index = next(
        (index for index, candidate in enumerate(ordered_items) if candidate.pk == item.pk),
        None,
    )
    if current_index is None:
        return False

    target_index = current_index - 1 if direction == "up" else current_index + 1
    if target_index < 0 or target_index >= len(ordered_items):
        return False

    ordered_items[current_index], ordered_items[target_index] = (
        ordered_items[target_index],
        ordered_items[current_index],
    )
    for position, playlist_item in enumerate(ordered_items):
        playlist_item.position = position
    PlaylistItem.objects.bulk_update(ordered_items, ["position"])
    return True
