from django.core.paginator import Paginator
from django.shortcuts import render

from .models import Category
from .services.video_browse import (
    VIDEO_BROWSE_SORTS,
    VIDEO_BROWSE_UPLOAD_FILTERS,
    browse_videos,
    normalize_browse_category,
    normalize_browse_upload,
)


VIDEO_BROWSE_PAGE_SIZE = 24


def video_browse(request):
    selected_category = normalize_browse_category(request.GET.get("category"))
    selected_upload = normalize_browse_upload(request.GET.get("uploaded", "any"))
    videos, selected_sort = browse_videos(
        request.user,
        request.GET.get("sort", "newest"),
        category=selected_category,
        uploaded=selected_upload,
    )
    page = Paginator(videos, VIDEO_BROWSE_PAGE_SIZE).get_page(request.GET.get("page"))
    return render(
        request,
        "videos/video_browse.html",
        {
            "videos": page,
            "selected_sort": selected_sort,
            "sort_options": VIDEO_BROWSE_SORTS,
            "categories": Category.objects.order_by("name", "pk"),
            "selected_category": selected_category,
            "selected_upload": selected_upload,
            "upload_filters": VIDEO_BROWSE_UPLOAD_FILTERS,
        },
    )
