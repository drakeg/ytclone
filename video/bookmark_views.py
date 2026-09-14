from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import VideoBookmark
from .services.bookmarks import get_visible_bookmarks


SAVED_MOMENTS_PAGE_SIZE = 24


@login_required
def video_bookmark_list(request):
    bookmarks = Paginator(
        get_visible_bookmarks(request.user),
        SAVED_MOMENTS_PAGE_SIZE,
    ).get_page(request.GET.get("page"))
    return render(
        request,
        "videos/video_bookmarks.html",
        {"bookmarks": bookmarks},
    )


@login_required
@require_POST
def video_bookmark_delete(request, pk):
    bookmark = get_object_or_404(VideoBookmark, pk=pk, user=request.user)
    video_pk = bookmark.video_id
    bookmark.delete()

    if request.POST.get("source") == "list":
        page = request.POST.get("page")
        if page:
            query = urlencode({"page": page})
            return redirect(f"{reverse('video_bookmark_list')}?{query}")
        return redirect("video_bookmark_list")

    return redirect("video_detail", pk=video_pk)
