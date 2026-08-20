from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .community_forms import CommunityPostForm, CommunityReplyForm
from .community_models import CommunityPost, CommunityReply
from .models import Channel


def channel_community(request, pk):
    channel = get_object_or_404(Channel, pk=pk)
    replies = CommunityReply.objects.select_related("author")
    posts = (
        CommunityPost.objects.filter(channel=channel)
        .select_related("author")
        .prefetch_related(Prefetch("replies", queryset=replies), "likes")
        .annotate(like_count=Count("likes", distinct=True), reply_count=Count("replies", distinct=True))
    )
    return render(
        request,
        "videos/channel_community.html",
        {
            "channel": channel,
            "posts": posts,
            "post_form": CommunityPostForm(),
            "reply_form": CommunityReplyForm(),
        },
    )


@login_required
@require_POST
def community_post_create(request, pk):
    channel = get_object_or_404(Channel, pk=pk)
    if request.user.pk != channel.owner_id:
        raise Http404("Channel not found")
    form = CommunityPostForm(request.POST)
    if form.is_valid():
        post = form.save(commit=False)
        post.channel = channel
        post.author = request.user
        post.save()
    return redirect("channel_community", pk=channel.pk)


@login_required
@require_POST
def community_post_like(request, post_pk):
    post = get_object_or_404(CommunityPost, pk=post_pk)
    if post.likes.filter(pk=request.user.pk).exists():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return redirect("channel_community", pk=post.channel_id)


@login_required
@require_POST
def community_reply_create(request, post_pk):
    post = get_object_or_404(CommunityPost.objects.select_related("channel"), pk=post_pk)
    form = CommunityReplyForm(request.POST)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.post = post
        reply.author = request.user
        reply.save()
    return redirect("channel_community", pk=post.channel_id)
