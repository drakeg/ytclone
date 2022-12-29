from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Video, Category, Comment, Channel
from django.contrib.auth.models import User
from .forms import CommentForm, EditProfileForm, VideoUploadForm

def video_list(request):
    videos_list = Video.objects.all()
    paginator = Paginator(videos_list, 10) # Show 10 videos per page
    page = request.GET.get('page')
    videos = paginator.get_page(page)
    return render(request, 'videos/video_list.html', {'videos': videos})

def video_detail(request, pk):
    video = get_object_or_404(Video, pk=pk)
    form = CommentForm()
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.video = video
            comment.save()
    comments = Comment.objects.filter(video=video)
    if request.user.id != video.author.id:
        video.views += 1
        video.save()
    return render(request, 'videos/video_detail.html', {'video': video, 'form': form, 'comments': comments})

@login_required
def like_video(request, pk):
    video = get_object_or_404(Video, pk=pk)
    if request.user in video.likes.all():
        video.likes.remove(request.user)
    else:
        video.likes.add(request.user)
    return redirect('video_detail', pk=video.pk)

@login_required
def dislike_video(request, pk):
    video = get_object_or_404(Video, pk=pk)
    if request.user in video.dislikes.all():
        video.dislikes.remove(request.user)
    else:
        video.dislikes.add(request.user)
    return redirect('video_detail', pk=video.pk)

def channel_list(request):
    channels = Channel.objects.all()
    return render(request, 'videos/channel_list.html', {'channels': channels})

def channel_detail(request, pk):
    channel = get_object_or_404(Channel, pk=pk)
    return render(request, 'videos/channel_detail.html', {'channel': channel})

@login_required
def subscribe(request, pk):
    channel = get_object_or_404(Channel, pk=pk)
    if request.user in channel.subscribers.all():
        channel.subscribers.remove(request.user)
    else:
        channel.subscribers.add(request.user)
    return redirect('channel_detail', pk=channel.pk)

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'videos/category_list.html', {'categories': categories})

def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    videos = Video.objects.filter(category=category)
    return render(request, 'videos/category_detail.html', {'category': category, 'videos': videos})

def search(request):
    query = request.GET.get('query')
    if query:
        videos = Video.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))
    else:
        videos = []
    return render(request, 'videos/search_results.html', {'videos': videos, 'query': query})

def filter_videos(request):
    category = request.GET.get('category')
    if category:
        videos = Video.objects.filter(category__name=category)
    else:
        videos = Video.objects.all()
    return render(request, 'videos/filter_results.html', {'videos': videos})

@login_required
def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    videos = Video.objects.filter(author=user)
    return render(request, 'videos/user_profile.html', {'user': user, 'videos': videos})

@login_required
def edit_profile(request, username):
    user = get_object_or_404(User, username=username)
    if request.method == "POST":
        form = EditProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_profile', username=user.username)
    else:
        form = EditProfileForm(instance=user)
    return render(request, 'videos/edit_profile.html', {'form': form})

@login_required
def upload_video(request):
    if request.method == "POST":
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.author = request.user
            video.save()
            return redirect('video_detail', pk=video.pk)
    else:
        form = VideoUploadForm()
    return render(request, 'videos/upload_video.html', {'form': form})
