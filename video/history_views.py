from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Video, WatchHistory


HISTORY_PAGE_SIZE = 24
HISTORY_QUERY_MAX_LENGTH = 120
HISTORY_SORTS = {
    "recent": ("-watched_at", "-pk"),
    "oldest": ("watched_at", "pk"),
    "title": ("video__title", "-watched_at", "-pk"),
}


def _clean_query(value):
    return str(value or "").strip()[:HISTORY_QUERY_MAX_LENGTH]


def _clean_sort(value):
    value = str(value or "recent")
    return value if value in HISTORY_SORTS else "recent"


def _history_url(*, page=None, query="", sort="recent"):
    params = {}
    if query:
        params["q"] = query
    if sort != "recent":
        params["sort"] = sort
    if page:
        params["page"] = page
    url = reverse("watch_history")
    return f"{url}?{urlencode(params)}" if params else url


@login_required
def watch_history(request):
    query = _clean_query(request.GET.get("q"))
    sort = _clean_sort(request.GET.get("sort"))
    entries = (
        request.user.watch_history.filter(
            video__in=Video.objects.visible_to(request.user)
        )
        .select_related("video", "video__author")
    )
    if query:
        entries = entries.filter(video__title__icontains=query)
    entries = entries.order_by(*HISTORY_SORTS[sort])
    page = Paginator(entries, HISTORY_PAGE_SIZE).get_page(request.GET.get("page"))
    return render(
        request,
        "videos/watch_history.html",
        {"entries": page, "history_query": query, "history_sort": sort},
    )


@login_required
@require_POST
def watch_history_remove(request, pk):
    entry = get_object_or_404(WatchHistory, pk=pk, user=request.user)
    entry.delete()
    return redirect(
        _history_url(
            page=request.POST.get("page"),
            query=_clean_query(request.POST.get("q")),
            sort=_clean_sort(request.POST.get("sort")),
        )
    )


@login_required
@require_POST
def watch_history_clear(request):
    request.user.watch_history.all().delete()
    return redirect("watch_history")
