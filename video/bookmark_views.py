from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import VideoBookmark
from .services.bookmarks import get_visible_bookmarks


SAVED_MOMENTS_PAGE_SIZE = 24
SAVED_MOMENTS_QUERY_MAX_LENGTH = 120


def _clean_query(value):
    return str(value or "").strip()[:SAVED_MOMENTS_QUERY_MAX_LENGTH]


def _bookmark_list_url(*, page=None, query=""):
    params = {}
    if query:
        params["q"] = query
    if page:
        params["page"] = page
    url = reverse("video_bookmark_list")
    if params:
        return f"{url}?{urlencode(params)}"
    return url


@login_required
def video_bookmark_list(request):
    query = _clean_query(request.GET.get("q"))
    visible_bookmarks = get_visible_bookmarks(request.user)
    if query:
        visible_bookmarks = visible_bookmarks.filter(
            Q(label__icontains=query) | Q(video__title__icontains=query)
        )

    bookmarks = Paginator(
        visible_bookmarks,
        SAVED_MOMENTS_PAGE_SIZE,
    ).get_page(request.GET.get("page"))
    return render(
        request,
        "videos/video_bookmarks.html",
        {"bookmarks": bookmarks, "bookmark_query": query},
    )


@login_required
@require_POST
def video_bookmark_delete(request, pk):
    bookmark = get_object_or_404(VideoBookmark, pk=pk, user=request.user)
    video_pk = bookmark.video_id
    bookmark.delete()

    if request.POST.get("source") == "list":
        return redirect(
            _bookmark_list_url(
                page=request.POST.get("page"),
                query=_clean_query(request.POST.get("q")),
            )
        )

    return redirect("video_detail", pk=video_pk)
