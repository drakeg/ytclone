from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .models import Video
from .services.channels import can_edit_video
from .services.short_clips import ShortClipError, create_short_from_video
from .shorts_forms import ShortClipForm


def shorts_feed(request):
    shorts = (
        Video.objects.visible_to(request.user)
        .filter(short_metadata__isnull=False)
        .select_related("author", "channel", "category")
        .prefetch_related("likes", "dislikes", "tags", "hashtags")
        .order_by("-pub_date", "-pk")[:50]
    )
    return render(request, "videos/shorts_feed.html", {"shorts": shorts})


@login_required
def create_short_from_long_form(request, pk):
    source_video = get_object_or_404(Video, pk=pk, deleted_at__isnull=True)
    if not can_edit_video(request.user, source_video):
        return HttpResponseForbidden("You cannot create a Short from this video.")
    if hasattr(source_video, "short_metadata"):
        return HttpResponseBadRequest("Create a Short from a standard video, not another Short.")

    form = ShortClipForm(
        request.POST or None,
        initial={
            "title": source_video.title[:255],
            "description": f"Short from {source_video.title}",
            "start_seconds": 0,
            "end_seconds": 60,
        },
    )
    if request.method == "POST" and form.is_valid():
        try:
            short = create_short_from_video(
                source_video=source_video,
                creator=request.user,
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                start_seconds=form.cleaned_data["start_seconds"],
                end_seconds=form.cleaned_data["end_seconds"],
            )
        except ShortClipError as error:
            form.add_error(None, str(error))
        else:
            return redirect("video_edit", pk=short.pk)

    return render(
        request,
        "videos/create_short_from_video.html",
        {"form": form, "source_video": source_video},
    )
