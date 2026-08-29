from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import CommentForm
from .models import Comment, Notification, Video
from .services.channels import can_edit_video
from .services.notifications import notify_comment, notify_reaction, notify_reply
from .services.short_clips import ShortClipError, create_short_from_video, rerender_short_from_source
from .shorts_forms import ShortClipForm
from .shorts_models import VideoShort


def shorts_feed(request):
    visible_replies = Comment.objects.filter(is_hidden=False).select_related("author").order_by("pub_date", "pk")
    visible_comments = (
        Comment.objects.filter(parent__isnull=True, is_hidden=False)
        .select_related("author")
        .prefetch_related(Prefetch("replies", queryset=visible_replies, to_attr="shorts_visible_replies"))
        .order_by("-pub_date", "-pk")
    )
    shorts = list(
        Video.objects.visible_to(request.user).filter(short_metadata__isnull=False)
        .select_related("author", "channel", "channel__owner", "category")
        .prefetch_related("likes", "dislikes", "tags", "hashtags", Prefetch("comment_set", queryset=visible_comments, to_attr="shorts_visible_comments"))
        .order_by("-pub_date", "-pk")[:50]
    )
    subscribed_channel_ids = set()
    if request.user.is_authenticated:
        subscribed_channel_ids = set(request.user.subscriptions.values_list("pk", flat=True))
    for short in shorts:
        short.viewer_is_subscribed = bool(short.channel_id and short.channel_id in subscribed_channel_ids)
        short.viewer_liked = bool(request.user.is_authenticated and request.user in short.likes.all())
        short.viewer_disliked = bool(request.user.is_authenticated and request.user in short.dislikes.all())
        short.shorts_recent_comments = short.shorts_visible_comments[:3]
        short.shorts_comment_count = len(short.shorts_visible_comments)
        for comment in short.shorts_recent_comments:
            comment.shorts_recent_replies = comment.shorts_visible_replies[-2:]
            comment.shorts_reply_count = len(comment.shorts_visible_replies)
    return render(request, "videos/shorts_feed.html", {"shorts": shorts})


def _visible_short_for_user(user, pk):
    return get_object_or_404(
        Video.objects.visible_to(user).filter(short_metadata__isnull=False),
        pk=pk,
    )


def _shorts_anchor(video_id):
    return f'{reverse("shorts_feed")}#short-{video_id}'


def _wants_json(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _reaction_payload(video, user):
    return {
        "liked": video.likes.filter(pk=user.pk).exists(),
        "disliked": video.dislikes.filter(pk=user.pk).exists(),
        "like_count": video.likes.count(),
        "dislike_count": video.dislikes.count(),
    }


def _short_comment_payload(comment):
    return {
        "id": comment.pk,
        "author": comment.author.username,
        "comment": comment.comment,
        "reply_url": reverse("add_short_reply", args=[comment.pk]),
        "comment_count": Comment.objects.filter(
            video=comment.video,
            parent__isnull=True,
            is_hidden=False,
        ).count(),
    }


def _short_reply_payload(reply):
    return {
        "id": reply.pk,
        "parent_id": reply.parent_id,
        "author": reply.author.username,
        "comment": reply.comment,
        "reply_count": Comment.objects.filter(parent=reply.parent, is_hidden=False).count(),
    }


@login_required
@require_POST
def like_short(request, pk):
    video = _visible_short_for_user(request.user, pk)
    if video.likes.filter(pk=request.user.pk).exists():
        video.likes.remove(request.user)
    else:
        video.dislikes.remove(request.user)
        video.likes.add(request.user)
        notify_reaction(video=video, actor=request.user, kind=Notification.Kind.LIKE)
    if _wants_json(request):
        return JsonResponse(_reaction_payload(video, request.user))
    return redirect(_shorts_anchor(video.pk))


@login_required
@require_POST
def dislike_short(request, pk):
    video = _visible_short_for_user(request.user, pk)
    if video.dislikes.filter(pk=request.user.pk).exists():
        video.dislikes.remove(request.user)
    else:
        video.likes.remove(request.user)
        video.dislikes.add(request.user)
        notify_reaction(video=video, actor=request.user, kind=Notification.Kind.DISLIKE)
    if _wants_json(request):
        return JsonResponse(_reaction_payload(video, request.user))
    return redirect(_shorts_anchor(video.pk))


@login_required
@require_POST
def add_short_comment(request, pk):
    video = _visible_short_for_user(request.user, pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.video = video
        comment.author = request.user
        comment.save()
        notify_comment(comment)
        if _wants_json(request):
            return JsonResponse(_short_comment_payload(comment), status=201)
    elif _wants_json(request):
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
    return redirect(_shorts_anchor(video.pk))


@login_required
@require_POST
def add_short_reply(request, pk):
    parent = get_object_or_404(
        Comment.objects.select_related("video", "video__author"),
        pk=pk,
        parent__isnull=True,
        is_hidden=False,
        video__short_metadata__isnull=False,
        video__in=Video.objects.visible_to(request.user),
    )
    form = CommentForm(request.POST)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.video = parent.video
        reply.author = request.user
        reply.parent = parent
        reply.save()
        notify_comment(reply)
        notify_reply(reply)
        if _wants_json(request):
            return JsonResponse(_short_reply_payload(reply), status=201)
    elif _wants_json(request):
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
    return redirect(_shorts_anchor(parent.video_id))


@login_required
def create_short_from_long_form(request, pk):
    source_video = get_object_or_404(Video, pk=pk, deleted_at__isnull=True)
    if not can_edit_video(request.user, source_video):
        return HttpResponseForbidden("You cannot create a Short from this video.")
    if hasattr(source_video, "short_metadata"):
        return HttpResponseBadRequest("Create a Short from a standard video, not another Short.")
    form = ShortClipForm(request.POST or None, initial={"title": source_video.title[:255], "description": f"Short from {source_video.title}", "start_seconds": 0, "end_seconds": 60, "thumbnail_frame_seconds": None, "reframing_mode": VideoShort.ReframingMode.VERTICAL_CENTER, "overlay_text": "", "overlay_position": VideoShort.OverlayPosition.BOTTOM})
    if request.method == "POST" and form.is_valid():
        try:
            short = create_short_from_video(source_video=source_video, creator=request.user, title=form.cleaned_data["title"], description=form.cleaned_data["description"], start_seconds=form.cleaned_data["start_seconds"], end_seconds=form.cleaned_data["end_seconds"], thumbnail_frame_seconds=form.cleaned_data["thumbnail_frame_seconds"], reframing_mode=form.cleaned_data["reframing_mode"], overlay_text=form.cleaned_data["overlay_text"], overlay_position=form.cleaned_data["overlay_position"])
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
    form = ShortClipForm(request.POST or None, initial={"title": short.title, "description": short.description, "start_seconds": metadata.source_start_seconds, "end_seconds": metadata.source_end_seconds, "thumbnail_frame_seconds": metadata.thumbnail_frame_seconds, "reframing_mode": metadata.reframing_mode, "overlay_text": metadata.overlay_text, "overlay_position": metadata.overlay_position})
    form.fields["title"].disabled = True
    form.fields["description"].disabled = True
    if request.method == "POST" and form.is_valid():
        try:
            rerender_short_from_source(short=short, start_seconds=form.cleaned_data["start_seconds"], end_seconds=form.cleaned_data["end_seconds"], thumbnail_frame_seconds=form.cleaned_data["thumbnail_frame_seconds"], reframing_mode=form.cleaned_data["reframing_mode"], overlay_text=form.cleaned_data["overlay_text"], overlay_position=form.cleaned_data["overlay_position"])
        except ShortClipError as error:
            form.add_error(None, str(error))
        else:
            return redirect("video_edit", pk=short.pk)
    return render(request, "videos/create_short_from_video.html", {"form": form, "source_video": source_video, "short": short, "rerender": True})
