from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CommentForm, EditProfileForm, VideoUploadForm
from .models import Category, Channel, Comment, Video


def video_list(request):
    videos_list = Video.objects.all()
    paginator = Paginator(videos_list, 10)
    page = request.GET.get("page")
    videos = paginator.get_page(page)
    return render(request, "videos/video_list.html", {"videos": videos})


def video_detail(request, pk):
    video = get_object_or_404(Video, pk=pk)
    comments = Comment.objects.filter(video=video)

    if request.user.id != video.author.id:
        video.views += 1
        video.save(update_fields=["views"])

    return render(
        request,
        "videos/video_detail.html",
        {"video": video, "form": CommentForm(), "comments": comments},
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
    return redirect("video_detail", pk=video.pk)


def channel_list(request):
    channels = Channel.objects.all()
    return render(request, "videos/channel_list.html", {"channels": channels})


def channel_detail(request, pk):
    channel = get_object_or_404(Channel, pk=pk)
    videos = Video.objects.filter(author=channel.owner)
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
    return redirect("channel_detail", pk=channel.pk)


def category_list(request):
    categories = Category.objects.all()
    return render(request, "videos/category_list.html", {"categories": categories})


def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    videos = Video.objects.filter(category=category)
    return render(
        request,
        "videos/category_detail.html",
        {"category": category, "videos": videos},
    )


def search(request):
    query = request.GET.get("query")
    if query:
        videos = Video.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    else:
        videos = []
    return render(
        request,
        "videos/search_results.html",
        {"videos": videos, "query": query},
    )


def filter_videos(request):
    category = request.GET.get("category")
    if category:
        videos = Video.objects.filter(category__name=category)
    else:
        videos = Video.objects.all()
    return render(request, "videos/filter_results.html", {"videos": videos})


def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    videos = Video.objects.filter(author=profile_user)
    return render(
        request,
        "videos/user_profile.html",
        {"user": profile_user, "videos": videos},
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
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.author = request.user
            video.save()
            return redirect("video_detail", pk=video.pk)
    else:
        form = VideoUploadForm()
    return render(request, "videos/upload_video.html", {"form": form})
