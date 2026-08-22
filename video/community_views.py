from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .community_forms import CommunityPostForm, CommunityReplyForm
from .community_models import (
    CommunityPollOption,
    CommunityPollVote,
    CommunityPost,
    CommunityReply,
)
from .models import Channel


def channel_community(request, pk):
    channel = get_object_or_404(Channel, pk=pk)
    replies = CommunityReply.objects.select_related("author")
    options = CommunityPollOption.objects.annotate(vote_count=Count("votes"))
    posts = (
        CommunityPost.objects.filter(channel=channel)
        .select_related("author", "featured_reply", "featured_reply__author")
        .prefetch_related(Prefetch("replies", queryset=replies), Prefetch("poll_options", queryset=options), "likes")
        .annotate(like_count=Count("likes", distinct=True), reply_count=Count("replies", distinct=True))
    )
    user_poll_votes = {}
    if request.user.is_authenticated:
        user_poll_votes = {
            vote.post_id: vote.option_id
            for vote in CommunityPollVote.objects.filter(user=request.user, post__channel=channel)
        }
    return render(
        request,
        "videos/channel_community.html",
        {
            "channel": channel,
            "posts": posts,
            "post_form": CommunityPostForm(),
            "reply_form": CommunityReplyForm(),
            "user_poll_votes": user_poll_votes,
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
        for position, text in enumerate(form.cleaned_data.get("poll_options", [])):
            CommunityPollOption.objects.create(post=post, text=text, position=position)
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


@login_required
@require_POST
def community_poll_vote(request, option_pk):
    option = get_object_or_404(CommunityPollOption.objects.select_related("post"), pk=option_pk)
    if option.post.kind != CommunityPost.Kind.POLL:
        raise Http404("Poll not found")
    CommunityPollVote.objects.update_or_create(
        post=option.post,
        user=request.user,
        defaults={"option": option},
    )
    return redirect("channel_community", pk=option.post.channel_id)


@login_required
@require_POST
def community_reply_feature(request, reply_pk):
    reply = get_object_or_404(CommunityReply.objects.select_related("post__channel"), pk=reply_pk)
    if reply.post.channel.owner_id != request.user.pk:
        raise Http404("Reply not found")
    reply.post.featured_reply = None if reply.post.featured_reply_id == reply.pk else reply
    reply.post.save(update_fields=["featured_reply", "updated_at"])
    return redirect("channel_community", pk=reply.post.channel_id)
