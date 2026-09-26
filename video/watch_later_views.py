from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import PlaylistItem, Video
from .services.watch_later import (
    WATCH_LATER_SORTS,
    completed_watch_later_video_ids,
    get_watch_later_playlist,
    move_watch_later_video,
    remove_from_watch_later,
    save_for_later,
    watch_later_videos,
)


WATCH_LATER_PAGE_SIZE = 24


def _clean_sort(value):
    value = str(value or "newest")
    return value if value in WATCH_LATER_SORTS else "newest"


@login_required
def watch_later(request):
    query = request.GET.get("q", "").strip()
    sort = _clean_sort(request.GET.get("sort"))
    videos = Paginator(
        watch_later_videos(request.user, query, sort),
        WATCH_LATER_PAGE_SIZE,
    ).get_page(request.GET.get("page"))
    completed_count = completed_watch_later_video_ids(request.user).count()
    return render(
        request,
        "videos/watch_later.html",
        {
            "videos": videos,
            "query": query,
            "sort": sort,
            "completed_watch_later_count": completed_count,
        },
    )


@login_required
@require_POST
def watch_later_add(request, pk):
    video = get_object_or_404(Video.objects.visible_to(request.user), pk=pk)
    save_for_later(request.user, video)
    return redirect(request.POST.get("next") or "watch_later")


@login_required
@require_POST
def watch_later_remove(request, pk):
    video = get_object_or_404(Video.objects.visible_to(request.user), pk=pk)
    remove_from_watch_later(request.user, video)

    if request.POST.get("source") == "watch_later":
        params = {}
        query = request.POST.get("q", "").strip()
        sort = _clean_sort(request.POST.get("sort"))
        page = request.POST.get("page", "").strip()
        if query:
            params["q"] = query
        if sort != "newest":
            params["sort"] = sort
        if page:
            params["page"] = page
        url = reverse("watch_later")
        return redirect(f"{url}?{urlencode(params)}" if params else url)

    return redirect(request.POST.get("next") or "watch_later")


@login_required
@require_POST
def watch_later_bulk_remove(request):
    selected_ids = []
    for raw_id in request.POST.getlist("video_ids"):
        try:
            selected_ids.append(int(raw_id))
        except (TypeError, ValueError):
            continue

    playlist = get_watch_later_playlist(request.user)
    if playlist is not None and selected_ids:
        visible_ids = Video.objects.visible_to(request.user).filter(
            pk__in=set(selected_ids)
        ).values_list("pk", flat=True)
        PlaylistItem.objects.filter(
            playlist=playlist,
            video_id__in=visible_ids,
        ).delete()

    params = {}
    query = request.POST.get("q", "").strip()
    sort = _clean_sort(request.POST.get("sort"))
    page = request.POST.get("page", "").strip()
    if query:
        params["q"] = query
    if sort != "newest":
        params["sort"] = sort
    if page:
        params["page"] = page
    url = reverse("watch_later")
    return redirect(f"{url}?{urlencode(params)}" if params else url)


@login_required
@require_POST
def watch_later_remove_completed(request):
    playlist = get_watch_later_playlist(request.user)
    if playlist is not None:
        completed_ids = completed_watch_later_video_ids(request.user)
        PlaylistItem.objects.filter(
            playlist=playlist,
            video_id__in=completed_ids,
        ).delete()

    params = {}
    query = request.POST.get("q", "").strip()
    sort = _clean_sort(request.POST.get("sort"))
    page = request.POST.get("page", "").strip()
    if query:
        params["q"] = query
    if sort != "newest":
        params["sort"] = sort
    if page:
        params["page"] = page
    url = reverse("watch_later")
    return redirect(f"{url}?{urlencode(params)}" if params else url)


@login_required
@require_POST
def watch_later_move(request, pk, direction):
    playlist = get_watch_later_playlist(request.user)
    if playlist is None:
        from django.http import Http404
        raise Http404("Watch Later item not found.")
    video = get_object_or_404(
        Video.objects.visible_to(request.user).filter(
            playlist_items__playlist=playlist
        ),
        pk=pk,
    )
    item = get_object_or_404(PlaylistItem, playlist=playlist, video=video)
    if direction not in {"up", "down"}:
        from django.http import Http404
        raise Http404("Invalid move direction.")
    move_watch_later_video(request.user, playlist, item, direction)

    params = {}
    query = request.POST.get("q", "").strip()
    page = request.POST.get("page", "").strip()
    if query:
        params["q"] = query
    params["sort"] = "manual"
    if page:
        params["page"] = page
    return redirect(f'{reverse("watch_later")}?{urlencode(params)}')
