from dataclasses import dataclass
from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from django.db.models import Case, Count, Exists, IntegerField, OuterRef, Q, QuerySet, Value, When
from django.utils import timezone

from ..metadata_models import Hashtag, Tag
from ..models import Channel, Playlist, Video
from .channel_access import available_channels


VIDEO_SORT_OPTIONS = {"relevance": "Relevance", "newest": "Newest", "oldest": "Oldest", "views": "Most viewed", "likes": "Most liked"}
VIDEO_CONTENT_FILTERS = {"all": "All", "video": "Standard videos", "short": "Shorts"}
VIDEO_UPLOAD_DATE_FILTERS = {"any": "Any time", "today": "Today", "week": "This week", "month": "This month", "year": "This year"}


@dataclass(frozen=True)
class SearchResults:
    query: str
    sort: str
    content_filter: str
    upload_date_filter: str
    videos: QuerySet
    channels: QuerySet
    playlists: QuerySet


def _upload_date_start(upload_date_filter: str):
    if upload_date_filter == "any":
        return None

    now = timezone.localtime(timezone.now())
    if upload_date_filter == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if upload_date_filter == "week":
        return now - timedelta(days=7)
    if upload_date_filter == "month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if upload_date_filter == "year":
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return None


def _video_results(query: str, sort: str, user, content_filter: str, upload_date_filter: str) -> QuerySet:
    hashtag_query = query[1:] if query.startswith("#") else query
    videos = (Video.objects.visible_to(user).select_related("author", "category").annotate(
        like_count=Count("likes", distinct=True),
        tag_exact=Exists(Tag.objects.filter(videos=OuterRef("pk"), name__iexact=query)),
        tag_contains=Exists(Tag.objects.filter(videos=OuterRef("pk"), name__icontains=query)),
        hashtag_exact=Exists(Hashtag.objects.filter(videos=OuterRef("pk"), name__iexact=hashtag_query)),
        hashtag_contains=Exists(Hashtag.objects.filter(videos=OuterRef("pk"), name__icontains=hashtag_query)),
    ).annotate(relevance=Case(
        When(title__iexact=query, then=Value(100)), When(title__icontains=query, then=Value(70)),
        When(tag_exact=True, then=Value(65)), When(hashtag_exact=True, then=Value(65)),
        When(author__username__iexact=query, then=Value(60)), When(category__name__iexact=query, then=Value(55)),
        When(tag_contains=True, then=Value(50)), When(hashtag_contains=True, then=Value(50)),
        When(author__username__icontains=query, then=Value(45)), When(category__name__icontains=query, then=Value(40)),
        When(description__icontains=query, then=Value(20)), default=Value(0), output_field=IntegerField(),
    )).filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(author__username__icontains=query) | Q(category__name__icontains=query) | Q(tag_contains=True) | Q(hashtag_contains=True)))

    if content_filter == "video":
        videos = videos.filter(short_metadata__isnull=True)
    elif content_filter == "short":
        videos = videos.filter(short_metadata__isnull=False)

    upload_date_start = _upload_date_start(upload_date_filter)
    if upload_date_start is not None:
        videos = videos.filter(pub_date__gte=upload_date_start)

    ordering = {"newest": ("-pub_date", "-pk"), "oldest": ("pub_date", "pk"), "views": ("-views", "-pub_date"), "likes": ("-like_count", "-pub_date"), "relevance": ("-relevance", "-views", "-pub_date")}
    return videos.order_by(*ordering[sort])


def _channel_results(query: str, user) -> QuerySet:
    return available_channels(user).select_related("owner").filter(Q(name__icontains=query) | Q(description__icontains=query)).annotate(subscriber_count=Count("subscribers", distinct=True)).order_by("-subscriber_count", "name")


def _playlist_results(query: str, user) -> QuerySet:
    visibility = Q(visibility=Playlist.Visibility.PUBLIC)
    if getattr(user, "is_authenticated", False): visibility |= Q(owner=user, visibility=Playlist.Visibility.UNLISTED)
    return Playlist.objects.select_related("owner").filter(visibility).filter(Q(name__icontains=query) | Q(description__icontains=query)).annotate(video_count=Count("items", distinct=True)).order_by("-updated_at", "name")


def search_content(query: str, sort: str, user=AnonymousUser(), content_filter="all", upload_date_filter="any") -> SearchResults:
    normalized_query = query.strip()
    normalized_sort = sort if sort in VIDEO_SORT_OPTIONS else "relevance"
    normalized_content_filter = content_filter if content_filter in VIDEO_CONTENT_FILTERS else "all"
    normalized_upload_date_filter = upload_date_filter if upload_date_filter in VIDEO_UPLOAD_DATE_FILTERS else "any"
    if not normalized_query:
        return SearchResults(
            query="",
            sort=normalized_sort,
            content_filter=normalized_content_filter,
            upload_date_filter=normalized_upload_date_filter,
            videos=Video.objects.none(),
            channels=Channel.objects.none(),
            playlists=Playlist.objects.none(),
        )
    return SearchResults(
        query=normalized_query,
        sort=normalized_sort,
        content_filter=normalized_content_filter,
        upload_date_filter=normalized_upload_date_filter,
        videos=_video_results(
            normalized_query,
            normalized_sort,
            user,
            normalized_content_filter,
            normalized_upload_date_filter,
        ),
        channels=_channel_results(normalized_query, user),
        playlists=_playlist_results(normalized_query, user),
    )


def search_suggestions(query: str, user=AnonymousUser(), limit: int = 8) -> list[str]:
    normalized_query = query.strip()
    if len(normalized_query) < 2 or limit < 1:
        return []

    visibility = Q(visibility=Playlist.Visibility.PUBLIC)
    if getattr(user, "is_authenticated", False):
        visibility |= Q(owner=user, visibility=Playlist.Visibility.UNLISTED)

    candidates = [
        *Video.objects.visible_to(user)
        .filter(title__icontains=normalized_query)
        .order_by("-views", "title")
        .values_list("title", flat=True)[:limit],
        *available_channels(user)
        .filter(name__icontains=normalized_query)
        .order_by("name")
        .values_list("name", flat=True)[:limit],
        *Playlist.objects.filter(visibility)
        .filter(name__icontains=normalized_query)
        .order_by("-updated_at", "name")
        .values_list("name", flat=True)[:limit],
    ]

    suggestions = []
    seen = set()
    for value in candidates:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        suggestions.append(value)
        if len(suggestions) == limit:
            break
    return suggestions
