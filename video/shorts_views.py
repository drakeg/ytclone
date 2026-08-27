from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .models import Video
from .services.channels import can_edit_video
from .services.short_clips import ShortClipError, create_short_from_video, rerender_short_from_source
from .shorts_forms import ShortClipForm
from .shorts_models import VideoShort


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
            "reframing_mode": VideoShort.ReframingMode.VERTICAL_CENTER,
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
                reframing_mode=form.cleaned_data["reframing_mode"],
            )
        except ShortClipError as error:
            form.add_error(None, str(error))
        else:
            return redirect("video_edit", pk=short.pk)

    return render(request, "videos/create_short_from_video.html", {"form": form, "source_video": source_video})


@login_required
def rerender_short(request, pk):
    short = get_object_or_404(Video, pk=pk, deleted_at__isnull=True)
    if not can_edit_video(request.user, short):
        return HttpResponseForbidden("You cannot re-render this Short.")
    try:
        metadata = short.short_metadata
    except VideoShort.DoesNotExist:
        return HttpResponseBadRequest("Only Shorts can be re-rendered.")
    if not metadata.source_video_id:
        return HttpResponseBadRequest("This Short was not generated from a source video.")

    source_video = metadata.source_video
    form = ShortClipForm(
        request.POST or None,
        initial={
            "title": short.title,
            "description": short.description,
            "start_seconds": metadata.source_start_seconds,
            "end_seconds": metadata.source_end_seconds,
            "reframing_mode": metadata.reframing_mode,
        },
    )
    form.fields["title"].disabled = True
    form.fields["description"].disabled = True

    if request.method == "POST" and form.is_valid():
        try:
            rerender_short_from_source(
                short=short,
                start_seconds=form.cleaned_data["start_seconds"],
                end_seconds=form.cleaned_data["end_seconds"],
                reframing_mode=form.cleaned_data["reframing_mode"],
            )
        except ShortClipError as error:
            form.add_error(None, str(error))
        else:
            return redirect("video_edit", pk=short.pk)

    return render(
        request,
        "videos/create_short_from_video.html",
        {"form": form, "source_video": source_video, "short": short, "rerender": True},
    )
