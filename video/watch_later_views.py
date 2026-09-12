from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Video
from .services.watch_later import remove_from_watch_later, save_for_later, watch_later_videos


@login_required
def watch_later(request):
    return render(
        request,
        "videos/watch_later.html",
        {"videos": watch_later_videos(request.user)},
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
    return redirect(request.POST.get("next") or "watch_later")
