from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import Playlist, Video


PLAYLIST_PAGE_SIZE = 24


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
