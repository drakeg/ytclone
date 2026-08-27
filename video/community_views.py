from django.contrib.auth.decorators import login_required
from django.db.models import Count, Exists, OuterRef, Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from monetization.models import ChannelMembershipSubscription

from .community_forms import CommunityPostForm, CommunityReplyForm
from .community_models import CommunityPollOption, CommunityPollVote, CommunityPost, CommunityReply
from .models import Channel
from .services.channels import accessible_channels
from .services.community_access import can_view_community_post, visible_community_posts
from .services.moderation_actions import set_community_reply_hidden


def channel_community(request, pk):
    channel = get_object_or_404(Channel, pk=pk)
    supporter_badge = ChannelMembershipSubscription.objects.filter(
        subscriber_id=OuterRef("author_id"),
        tier__monetization_account__channel=channel,
        status=ChannelMembershipSubscription.Status.ACTIVE,
        show_supporter_badge=True,
    )
    replies = CommunityReply.objects.select_related("author")
    if channel.owner_id != getattr(request.user, "pk", None) and not (
        request.user.is_authenticated and accessible_channels(request.user).filter(pk=channel.pk).exists()
    ):
        replies = replies.filter(moderation_state__isnull=True)
    replies = replies.annotate(show_supporter_badge=Exists(supporter_badge))
    options = CommunityPollOption.objects.annotate(vote_count=Count("votes"))
    posts = visible_community_posts(request.user, channel).select_related(
        "author", "featured_reply", "featured_reply__author"
    ).prefetch_related(
        Prefetch("replies", queryset=replies), Prefetch("poll_options", queryset=options), "likes"
    ).annotate(like_count=Count("likes", distinct=True), reply_count=Count("replies", distinct=True))
    user_poll_votes = {}
    if request.user.is_authenticated:
        user_poll_votes = {vote.post_id: vote.option_id for vote in CommunityPollVote.objects.filter(user=request.user, post__in=posts)}
    return render(request, "videos/channel_community.html", {
        "channel": channel,
        "posts": posts,
        "post_form": CommunityPostForm(),
        "reply_form": CommunityReplyForm(),
        "user_poll_votes": user_poll_votes,
        "may_moderate_community": request.user.is_authenticated and accessible_channels(request.user).filter(pk=channel.pk).exists(),
    })


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


def _visible_post_or_404(user, post_pk):
    post = get_object_or_404(CommunityPost.objects.select_related("channel"), pk=post_pk)
    if not can_view_community_post(user, post):
        raise Http404("Community post not found")
    return post


@login_required
@require_POST
def community_post_like(request, post_pk):
    post = _visible_post_or_404(request.user, post_pk)
    if post.likes.filter(pk=request.user.pk).exists(): post.likes.remove(request.user)
    else: post.likes.add(request.user)
    return redirect("channel_community", pk=post.channel_id)


@login_required
@require_POST
def community_reply_create(request, post_pk):
    post = _visible_post_or_404(request.user, post_pk)
    form = CommunityReplyForm(request.POST)
    if form.is_valid():
        reply = form.save(commit=False); reply.post = post; reply.author = request.user; reply.save()
    return redirect("channel_community", pk=post.channel_id)


@login_required
@require_POST
def community_poll_vote(request, option_pk):
    option = get_object_or_404(CommunityPollOption.objects.select_related("post__channel"), pk=option_pk)
    if option.post.kind != CommunityPost.Kind.POLL or not can_view_community_post(request.user, option.post):
        raise Http404("Poll not found")
    CommunityPollVote.objects.update_or_create(post=option.post, user=request.user, defaults={"option": option})
    return redirect("channel_community", pk=option.post.channel_id)


@login_required
@require_POST
def community_reply_feature(request, reply_pk):
    reply = get_object_or_404(
        CommunityReply.objects.select_related("post__channel"),
        pk=reply_pk,
        moderation_state__isnull=True,
    )
    if reply.post.channel.owner_id != request.user.pk:
        raise Http404("Reply not found")
    reply.post.featured_reply = None if reply.post.featured_reply_id == reply.pk else reply
    reply.post.save(update_fields=["featured_reply", "updated_at"])
    return redirect("channel_community", pk=reply.post.channel_id)


@login_required
@require_POST
def community_reply_moderate(request, reply_pk):
    reply = get_object_or_404(CommunityReply.objects.select_related("post__channel"), pk=reply_pk)
    if not accessible_channels(request.user).filter(pk=reply.post.channel_id).exists():
        raise Http404("Reply not found")
    action = request.POST.get("action")
    if action not in {"hide", "restore"}:
        raise Http404("Invalid action")
    set_community_reply_hidden(actor=request.user, reply=reply, hidden=action == "hide", audit=False)
    return redirect("channel_community", pk=reply.post.channel_id)
