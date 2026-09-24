from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Playlist, PlaylistItem, Video
from .services.playlist_ordering import move_playlist_item


PLAYLIST_PAGE_SIZE = 24
PLAYLIST_QUERY_MAX_LENGTH = 120
PLAYLIST_SORTS = {
    "recent": ("-updated_at", "-pk"),
    "oldest": ("updated_at", "pk"),
    "name": ("name", "-updated_at", "-pk"),
}


def _clean_playlist_query(value):
    return (value or "").strip()[:PLAYLIST_QUERY_MAX_LENGTH]


def _clean_playlist_sort(value):
    value = str(value or "recent")
    return value if value in PLAYLIST_SORTS else "recent"


@login_required
def playlist_list(request):
    query = _clean_playlist_query(request.GET.get("q"))
    sort = _clean_playlist_sort(request.GET.get("sort"))
    playlists = request.user.playlists.prefetch_related("items__video")
    if query:
        playlists = playlists.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    playlists = playlists.order_by(*PLAYLIST_SORTS[sort])
    page = Paginator(playlists, PLAYLIST_PAGE_SIZE).get_page(request.GET.get("page"))
    return render(
        request,
        "videos/playlist_list.html",
        {"playlists": page, "query": query, "sort": sort},
    )


def playlist_detail(request, pk):
    playlist = get_object_or_404(
        Playlist.objects.select_related("owner"),
        pk=pk,
    )
    if not playlist.can_view(request.user):
        raise Http404("Playlist not found")

    visible_items = (
        playlist.items.filter(video__in=Video.objects.visible_to(request.user))
        .select_related("video", "video__author", "video__channel", "video__category")
        .order_by("position", "added_at", "pk")
    )
    visible_items_page = Paginator(visible_items, PLAYLIST_PAGE_SIZE).get_page(
        request.GET.get("page")
    )
    return render(
        request,
        "videos/playlist_detail.html",
        {
            "playlist": playlist,
            "visible_items": visible_items_page,
        },
    )


@login_required
@require_POST
def playlist_reorder_item(request, pk, item_pk, direction):
    playlist = get_object_or_404(Playlist, pk=pk, owner=request.user)
    item = get_object_or_404(PlaylistItem, pk=item_pk, playlist=playlist)
    move_playlist_item(
        playlist=playlist,
        item=item,
        user=request.user,
        direction=direction,
    )
    redirect_url = redirect("playlist_detail", pk=playlist.pk)
    page = request.POST.get("page", "").strip()
    if page.isdigit() and int(page) > 1:
        redirect_url["Location"] = f"{redirect_url['Location']}?page={int(page)}"
    return redirect_url
