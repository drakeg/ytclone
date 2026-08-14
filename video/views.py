import json
import math
import uuid

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import F, Max
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CommentForm, EditProfileForm, PlaylistForm, VideoEditForm, VideoUploadForm
from .models import (
    Category,
    Channel,
    Comment,
    Notification,
    Playlist,
    PlaylistItem,
    Video,
    WatchHistory,
)
from .services.analytics import get_channel_analytics, get_creator_analytics
from .services.discovery import get_discovery_sections
from .services.notifications import notify_comment, notify_new_upload, notify_reaction, notify_subscription
from .services.search import VIDEO_SORT_OPTIONS, search_content


VIEWED_VIDEOS_SESSION_KEY = "viewed_video_ids"


def video_list(request):
    sections = get_discovery_sections(request.user)
    return render(request, "videos/video_list.html", {"sections": sections})


@login_required
def creator_analytics(request):
    analytics = get_creator_analytics(request.user)
    return render(
        request,
        "videos/creator_analytics.html",
        {"analytics": analytics},
    )


@login_required
def channel_analytics(request, pk):
    channel = get_object_or_404(Channel, pk=pk, owner=request.user)
    analytics = get_channel_analytics(channel)
    return render(
        request,
        "videos/channel_analytics.html",
        {"analytics": analytics, "channel": channel},
    )


@login_required
def notification_list(request):
    notifications = request.user.notifications.select_related(
        "actor", "video", "channel"
    )
    return render(
        request,
        "videos/notification_list.html",
        {"notifications": notifications},
    )


@login_required
@require_POST
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return redirect("notification_list")


@login_required
@require_POST
def notification_mark_all_read(request):
    request.user.notifications.filter(read_at__isnull=True).update(
        read_at=timezone.now()
    )
    return redirect("notification_list")


def video_detail(request, pk):
    video = get_object_or_404(Video.objects.visible_to(request.user), pk=pk)
    return _render_video_detail(request, video)


def shared_video_detail(request, token):
    video = get_object_or_404(
        Video.objects.select_related("author", "channel", "category"),
        share_token=token,
        publication_status=Video.PublicationStatus.UNLISTED,
    )
    return _render_video_detail(request, video)


def _render_video_detail(request, video):
    comments = Comment.objects.filter(video=video)
    playlists = []
    history_entry = None
    if request.user.is_authenticated:
        playlists = request.user.playlists.all()
        history_entry, unused = WatchHistory.objects.update_or_create(
            user=request.user,
            video=video,
            defaults={"watched_at": timezone.now()},
        )

    viewed_video_ids = request.session.get(VIEWED_VIDEOS_SESSION_KEY, [])
    is_owner = request.user.is_authenticated and request.user.pk == video.author_id

    if not is_owner and video.pk not in viewed_video_ids:
        Video.objects.filter(pk=video.pk).update(views=F("views") + 1)
        viewed_video_ids.append(video.pk)
        request.session[VIEWED_VIDEOS_SESSION_KEY] = viewed_video_ids
        video.refresh_from_db(fields=["views"])

    return render(
        request,
        "videos/video_detail.html",
        {
            "video": video,
            "form": CommentForm(),
            "comments": comments,
            "playlists": playlists,
            "history_entry": history_entry,
        },
    )


@login_required
@require_POST
def video_rotate_share_token(request, pk):
    video = get_object_or_404(Video, pk=pk, author=request.user)
    video.share_token = uuid.uuid4()
    video.save(update_fields=["share_token"])
    return redirect("video_detail", pk=video.pk)


@login_required
@require_POST
def playback_progress(request, pk):
    video = get_object_or_404(Video, pk=pk)
    try:
        payload = json.loads(request.body)
        position = float(payload["position_seconds"])
        duration = float(payload["duration_seconds"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return JsonResponse({"error": "Invalid playback progress."}, status=400)

    if not math.isfinite(position) or not math.isfinite(duration) or duration <= 0:
        return JsonResponse({"error": "Invalid playback progress."}, status=400)

    duration_seconds = max(1, round(duration))
    position_seconds = min(max(0, round(position)), duration_seconds)
    entry, unused = WatchHistory.objects.update_or_create(
        user=request.user,
        video=video,
        defaults={
            "playback_position_seconds": position_seconds,
            "duration_seconds": duration_seconds,
        },
    )
    return JsonResponse(
        {
            "position_seconds": entry.playback_position_seconds,
            "duration_seconds": entry.duration_seconds,
        }
    )


@login_required
@require_POST
def add_comment(request, pk):
    video = get_object_or_404(Video, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.video = video
        comment.author = request.user
        comment.save()
        notify_comment(comment)
    return redirect("video_detail", pk=video.pk)


@login_required
@require_POST
def like_video(request, pk):
    video = get_object_or_404(Video, pk=pk)
    if video.likes.filter(pk=request.user.pk).exists():
        video.likes.remove(request.user)
    else:
        video.dislikes.remove(request.user)
        video.likes.add(request.user)
        notify_reaction(
            video=video,
            actor=request.user,
            kind=Notification.Kind.LIKE,
        )
    return redirect("video_detail", pk=video.pk)


@login_required
@require_POST
def dislike_video(request, pk):
    video = get_object_or_404(Video, pk=pk)
    if video.dislikes.filter(pk=request.user.pk).exists():
        video.dislikes.remove(request.user)
    else:
        video.likes.remove(request.user)
        video.dislikes.add(request.user)
        notify_reaction(
            video=video,
            actor=request.user,
            kind=Notification.Kind.DISLIKE,
        )
    return redirect("video_detail", pk=video.pk)


def channel_list(request):
    channels = Channel.objects.all()
    return render(request, "videos/channel_list.html", {"channels": channels})


def channel_detail(request, pk):
    channel = get_object_or_404(Channel, pk=pk)
    videos = channel.videos.visible_to(request.user).select_related("author", "category")
    return render(
        request,
        "videos/channel_detail.html",
        {"channel": channel, "videos": videos},
    )


@login_required
@require_POST
def subscribe(request, pk):
    channel = get_object_or_404(Channel, pk=pk)
    if request.user in channel.subscribers.all():
        channel.subscribers.remove(request.user)
    else:
        channel.subscribers.add(request.user)
        notify_subscription(channel=channel, actor=request.user)
    return redirect("channel_detail", pk=channel.pk)


def category_list(request):
    categories = Category.objects.all()
    return render(request, "videos/category_list.html", {"categories": categories})


def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    videos = Video.objects.visible_to(request.user).filter(category=category)
    return render(
        request,
        "videos/category_detail.html",
        {"category": category, "videos": videos},
    )


def search(request):
    results = search_content(
        request.GET.get("query", ""),
        request.GET.get("sort", "relevance"),
        request.user,
    )
    return render(
        request,
        "videos/search_results.html",
        {
            "query": results.query,
            "selected_sort": results.sort,
            "sort_options": VIDEO_SORT_OPTIONS,
            "videos": results.videos,
            "channels": results.channels,
            "playlists": results.playlists,
        },
    )


def filter_videos(request):
    category = request.GET.get("category")
    if category:
        videos = Video.objects.visible_to(request.user).filter(category__name=category)
    else:
        videos = Video.objects.visible_to(request.user)
    return render(request, "videos/filter_results.html", {"videos": videos})


def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    videos = Video.objects.visible_to(request.user).filter(author=profile_user)
    public_playlists = profile_user.playlists.filter(
        visibility=Playlist.Visibility.PUBLIC
    )
    return render(
        request,
        "videos/user_profile.html",
        {
            "user": profile_user,
            "videos": videos,
            "public_playlists": public_playlists,
        },
    )


@login_required
def edit_profile(request, username):
    user = get_object_or_404(User, username=username, pk=request.user.pk)
    if request.method == "POST":
        form = EditProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect("user_profile", username=user.username)
    else:
        form = EditProfileForm(instance=user)
    return render(request, "videos/edit_profile.html", {"form": form})


@login_required
def upload_video(request):
    if request.method == "POST":
        form = VideoUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            video = form.save(commit=False)
            video.author = request.user
            video.save()
            if video.publication_status == Video.PublicationStatus.PUBLISHED:
                notify_new_upload(video)
            return redirect("video_detail", pk=video.pk)
    else:
        form = VideoUploadForm(user=request.user)
    return render(request, "videos/upload_video.html", {"form": form})


@login_required
def video_edit(request, pk):
    video = get_object_or_404(Video, pk=pk, author=request.user)
    if request.method == "POST":
        form = VideoEditForm(
            request.POST, request.FILES, instance=video, user=request.user
        )
        if form.is_valid():
            form.save()
            return redirect("video_detail", pk=video.pk)
    else:
        form = VideoEditForm(instance=video, user=request.user)
    return render(request, "videos/video_edit.html", {"form": form, "video": video})


@login_required
def video_delete(request, pk):
    video = get_object_or_404(Video, pk=pk, author=request.user)
    if request.method == "POST":
        video.delete()
        return redirect("video_list")
    return render(request, "videos/video_confirm_delete.html", {"video": video})


@login_required
def playlist_list(request):
    playlists = request.user.playlists.prefetch_related("items__video")
    return render(request, "videos/playlist_list.html", {"playlists": playlists})


@login_required
def playlist_create(request):
    if request.method == "POST":
        form = PlaylistForm(request.POST)
        if form.is_valid():
            playlist = form.save(commit=False)
            playlist.owner = request.user
            playlist.save()
            return redirect("playlist_detail", pk=playlist.pk)
    else:
        form = PlaylistForm()
    return render(
        request,
        "videos/playlist_form.html",
        {"form": form, "heading": "Create Playlist"},
    )


def playlist_detail(request, pk):
    playlist = get_object_or_404(
        Playlist.objects.select_related("owner").prefetch_related("items__video"),
        pk=pk,
    )
    if not playlist.can_view(request.user):
        raise Http404("Playlist not found")
    visible_items = playlist.items.filter(
        video__in=Video.objects.visible_to(request.user)
    ).select_related("video")
    return render(request, "videos/playlist_detail.html", {"playlist": playlist, "visible_items": visible_items})


@login_required
def playlist_edit(request, pk):
    playlist = get_object_or_404(Playlist, pk=pk, owner=request.user)
    if request.method == "POST":
        form = PlaylistForm(request.POST, instance=playlist)
        if form.is_valid():
            form.save()
            return redirect("playlist_detail", pk=playlist.pk)
    else:
        form = PlaylistForm(instance=playlist)
    return render(
        request,
        "videos/playlist_form.html",
        {"form": form, "heading": "Edit Playlist"},
    )


@login_required
@require_POST
def playlist_delete(request, pk):
    playlist = get_object_or_404(Playlist, pk=pk, owner=request.user)
    playlist.delete()
    return redirect("playlist_list")


@login_required
@require_POST
def playlist_add_video(request, pk, video_pk):
    playlist = get_object_or_404(Playlist, pk=pk, owner=request.user)
    video = get_object_or_404(Video, pk=video_pk)
    next_position = (
        playlist.items.aggregate(max_position=Max("position"))["max_position"] or 0
    ) + 1
    PlaylistItem.objects.get_or_create(
        playlist=playlist,
        video=video,
        defaults={"position": next_position},
    )
    return redirect("playlist_detail", pk=playlist.pk)


@login_required
@require_POST
def playlist_remove_video(request, pk, item_pk):
    playlist = get_object_or_404(Playlist, pk=pk, owner=request.user)
    item = get_object_or_404(PlaylistItem, pk=item_pk, playlist=playlist)
    item.delete()
    return redirect("playlist_detail", pk=playlist.pk)


@login_required
def watch_history(request):
    entries = request.user.watch_history.filter(
        video__in=Video.objects.visible_to(request.user)
    ).select_related("video", "video__author")
    return render(request, "videos/watch_history.html", {"entries": entries})


@login_required
@require_POST
def watch_history_remove(request, pk):
    entry = get_object_or_404(WatchHistory, pk=pk, user=request.user)
    entry.delete()
    return redirect("watch_history")


@login_required
@require_POST
def watch_history_clear(request):
    request.user.watch_history.all().delete()
    return redirect("watch_history")
