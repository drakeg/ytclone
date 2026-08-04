from dataclasses import dataclass

from django.contrib.auth.models import AnonymousUser
from django.db.models import Case, Count, IntegerField, Q, QuerySet, Value, When

from ..models import Channel, Playlist, Video


VIDEO_SORT_OPTIONS = {
    "relevance": "Relevance",
    "newest": "Newest",
    "oldest": "Oldest",
    "views": "Most viewed",
    "likes": "Most liked",
}


@dataclass(frozen=True)
class SearchResults:
    query: str
    sort: str
    videos: QuerySet
    channels: QuerySet
    playlists: QuerySet


def _video_results(query: str, sort: str) -> QuerySet:
    videos = (
        Video.objects.select_related("author", "category")
        .annotate(
            like_count=Count("likes", distinct=True),
            relevance=Case(
                When(title__iexact=query, then=Value(100)),
                When(title__icontains=query, then=Value(70)),
                When(author__username__iexact=query, then=Value(60)),
                When(category__name__iexact=query, then=Value(55)),
                When(author__username__icontains=query, then=Value(45)),
                When(category__name__icontains=query, then=Value(40)),
                When(description__icontains=query, then=Value(20)),
                default=Value(0),
                output_field=IntegerField(),
            ),
        )
        .filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(author__username__icontains=query)
            | Q(category__name__icontains=query)
        )
        .distinct()
    )

    ordering = {
        "newest": ("-pub_date", "-pk"),
        "oldest": ("pub_date", "pk"),
        "views": ("-views", "-pub_date"),
        "likes": ("-like_count", "-pub_date"),
        "relevance": ("-relevance", "-views", "-pub_date"),
    }
    return videos.order_by(*ordering[sort])


def _channel_results(query: str) -> QuerySet:
    return (
        Channel.objects.select_related("owner")
        .filter(Q(name__icontains=query) | Q(description__icontains=query))
        .annotate(subscriber_count=Count("subscribers", distinct=True))
        .order_by("-subscriber_count", "name")
    )


def _playlist_results(query: str, user) -> QuerySet:
    visibility = Q(visibility=Playlist.Visibility.PUBLIC)
    if getattr(user, "is_authenticated", False):
        visibility |= Q(owner=user, visibility=Playlist.Visibility.UNLISTED)

    return (
        Playlist.objects.select_related("owner")
        .filter(visibility)
        .filter(Q(name__icontains=query) | Q(description__icontains=query))
        .annotate(video_count=Count("items", distinct=True))
        .order_by("-updated_at", "name")
    )


def search_content(query: str, sort: str, user=AnonymousUser()) -> SearchResults:
    normalized_query = query.strip()
    normalized_sort = sort if sort in VIDEO_SORT_OPTIONS else "relevance"

    if not normalized_query:
        return SearchResults(
            query="",
            sort=normalized_sort,
            videos=Video.objects.none(),
            channels=Channel.objects.none(),
            playlists=Playlist.objects.none(),
        )

    return SearchResults(
        query=normalized_query,
        sort=normalized_sort,
        videos=_video_results(normalized_query, normalized_sort),
        channels=_channel_results(normalized_query),
        playlists=_playlist_results(normalized_query, user),
    )
