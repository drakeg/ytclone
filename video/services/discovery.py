from dataclasses import dataclass

from django.db.models import Count, F, Max, QuerySet

from video.models import Playlist, Video


DISCOVERY_SECTION_LIMIT = 4


@dataclass(frozen=True)
class DiscoverySections:
    newest_videos: QuerySet
    most_viewed_videos: QuerySet
    most_liked_videos: QuerySet
    recently_watched_videos: QuerySet
    continue_watching_videos: QuerySet
    public_playlists: QuerySet


def get_discovery_sections(user, limit=DISCOVERY_SECTION_LIMIT):
    videos = Video.objects.select_related("author", "category")
    recently_watched = Video.objects.none()
    continue_watching = Video.objects.none()

    if user.is_authenticated:
        recently_watched = (
            videos.filter(history_entries__user=user)
            .annotate(last_watched_at=Max("history_entries__watched_at"))
            .order_by("-last_watched_at", "-pk")[:limit]
        )
        continue_watching = (
            videos.filter(
                history_entries__user=user,
                history_entries__playback_position_seconds__gt=0,
                history_entries__duration_seconds__gt=0,
            )
            .annotate(
                resume_position_seconds=F(
                    "history_entries__playback_position_seconds"
                ),
                playback_duration_seconds=F("history_entries__duration_seconds"),
                remaining_seconds=(
                    F("history_entries__duration_seconds")
                    - F("history_entries__playback_position_seconds")
                ),
                last_watched_at=Max("history_entries__watched_at"),
            )
            .filter(remaining_seconds__gt=5)
            .order_by("-last_watched_at", "-pk")[:limit]
        )

    return DiscoverySections(
        newest_videos=videos.order_by("-pub_date", "-pk")[:limit],
        most_viewed_videos=videos.order_by("-views", "-pub_date", "-pk")[:limit],
        most_liked_videos=(
            videos.annotate(like_count=Count("likes", distinct=True))
            .order_by("-like_count", "-views", "-pub_date", "-pk")[:limit]
        ),
        recently_watched_videos=recently_watched,
        continue_watching_videos=continue_watching,
        public_playlists=(
            Playlist.objects.filter(visibility=Playlist.Visibility.PUBLIC)
            .select_related("owner")
            .annotate(video_count=Count("items", distinct=True))
            .order_by("-updated_at", "name", "-pk")[:limit]
        ),
    )
