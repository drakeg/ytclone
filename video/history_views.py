from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Video, WatchHistory


HISTORY_PAGE_SIZE = 24


@login_required
def watch_history(request):
    entries = (
        request.user.watch_history.filter(
            video__in=Video.objects.visible_to(request.user)
        )
        .select_related("video", "video__author")
        .order_by("-watched_at", "-pk")
    )
    page = Paginator(entries, HISTORY_PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "videos/watch_history.html", {"entries": page})


@login_required
@require_POST
def watch_history_remove(request, pk):
    entry = get_object_or_404(WatchHistory, pk=pk, user=request.user)
    entry.delete()
    page = request.POST.get("page")
    if page:
        return redirect(f"/videos/history/?page={page}")
    return redirect("watch_history")


@login_required
@require_POST
def watch_history_clear(request):
    request.user.watch_history.all().delete()
    return redirect("watch_history")
