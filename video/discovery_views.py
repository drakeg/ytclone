from django.core.paginator import Paginator
from django.shortcuts import render

from .services.video_browse import VIDEO_BROWSE_SORTS, browse_videos


VIDEO_BROWSE_PAGE_SIZE = 24


def video_browse(request):
    videos, selected_sort = browse_videos(request.user, request.GET.get("sort", "newest"))
    page = Paginator(videos, VIDEO_BROWSE_PAGE_SIZE).get_page(request.GET.get("page"))
    return render(
        request,
        "videos/video_browse.html",
        {
            "videos": page,
            "selected_sort": selected_sort,
            "sort_options": VIDEO_BROWSE_SORTS,
        },
    )
