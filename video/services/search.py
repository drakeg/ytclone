from dataclasses import dataclass

from django.contrib.auth.models import AnonymousUser
from django.db.models import Case, Count, Exists, IntegerField, OuterRef, Q, QuerySet, Value, When

from ..metadata_models import Hashtag, Tag
from ..models import Channel, Playlist, Video
from .channel_access import available_channels


VIDEO_SORT_OPTIONS = {"relevance": "Relevance", "newest": "Newest", "oldest": "Oldest", "views": "Most viewed", "likes": "Most liked"}


@dataclass(frozen=True)
class SearchResults:
    query: str
    sort: str
    videos: QuerySet
    channels: QuerySet
    playlists: QuerySet


def _video_results(query: str, sort: str, user) -> QuerySet:
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
    ordering = {"newest": ("-pub_date", "-pk"), "oldest": ("pub_date", "pk"), "views": ("-views", "-pub_date"), "likes": ("-like_count", "-pub_date"), "relevance": ("-relevance", "-views", "-pub_date")}
    return videos.order_by(*ordering[sort])


def _channel_results(query: str, user) -> QuerySet:
    return available_channels(user).select_related("owner").filter(Q(name__icontains=query) | Q(description__icontains=query)).annotate(subscriber_count=Count("subscribers", distinct=True)).order_by("-subscriber_count", "name")


def _playlist_results(query: str, user) -> QuerySet:
    visibility = Q(visibility=Playlist.Visibility.PUBLIC)
    if getattr(user, "is_authenticated", False): visibility |= Q(owner=user, visibility=Playlist.Visibility.UNLISTED)
    return Playlist.objects.select_related("owner").filter(visibility).filter(Q(name__icontains=query) | Q(description__icontains=query)).annotate(video_count=Count("items", distinct=True)).order_by("-updated_at", "name")


def search_content(query: str, sort: str, user=AnonymousUser()) -> SearchResults:
    normalized_query = query.strip(); normalized_sort = sort if sort in VIDEO_SORT_OPTIONS else "relevance"
    if not normalized_query:
        return SearchResults(query="", sort=normalized_sort, videos=Video.objects.none(), channels=Channel.objects.none(), playlists=Playlist.objects.none())
    return SearchResults(query=normalized_query, sort=normalized_sort, videos=_video_results(normalized_query, normalized_sort, user), channels=_channel_results(normalized_query, user), playlists=_playlist_results(normalized_query, user))
