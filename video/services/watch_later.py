from django.db.models import Max

from ..models import Playlist, PlaylistItem, Video


WATCH_LATER_NAME = "Watch Later"


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


def watch_later_videos(user):
    playlist = get_watch_later_playlist(user)
    if playlist is None:
        return Video.objects.none()

    return (
        Video.objects.visible_to(user)
        .filter(playlist_items__playlist=playlist)
        .select_related("author", "category", "channel")
        .prefetch_related("hashtags")
        .order_by("-playlist_items__added_at", "-playlist_items__pk")
    )
