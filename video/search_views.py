from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .services.search import VIDEO_SORT_OPTIONS, search_content, search_suggestions


VIDEO_PAGE_SIZE = 12
CHANNEL_PAGE_SIZE = 6
PLAYLIST_PAGE_SIZE = 6


def _bounded_page(queryset, raw_page, per_page):
    paginator = Paginator(queryset, per_page)
    try:
        page_number = int(raw_page or 1)
    except (TypeError, ValueError):
        page_number = 1
    page_number = max(1, min(page_number, paginator.num_pages))
    return paginator.page(page_number)


def search(request):
    results = search_content(
        request.GET.get("query", ""),
        request.GET.get("sort", "relevance"),
        request.user,
    )
    videos = _bounded_page(
        results.videos, request.GET.get("video_page"), VIDEO_PAGE_SIZE
    )
    channels = _bounded_page(
        results.channels, request.GET.get("channel_page"), CHANNEL_PAGE_SIZE
    )
    playlists = _bounded_page(
        results.playlists, request.GET.get("playlist_page"), PLAYLIST_PAGE_SIZE
    )
    return render(
        request,
        "videos/search_results.html",
        {
            "query": results.query,
            "selected_sort": results.sort,
            "sort_options": VIDEO_SORT_OPTIONS,
            "videos": videos,
            "channels": channels,
            "playlists": playlists,
        },
    )


@require_GET
def suggestions(request):
    return JsonResponse(
        {"suggestions": search_suggestions(request.GET.get("query", ""), request.user)}
    )
