from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .community_models import CommunityPost, CommunityReply
from .models import Channel, Video
from .services.administration import get_creator_audience, get_site_admin_overview, moderate_site_comment
from .services.moderation_actions import (
    restore_video,
    set_channel_suspended,
    set_community_post_hidden,
    set_community_reply_hidden,
    set_user_active,
    take_down_video,
)

User = get_user_model()


@staff_member_required
def site_admin_dashboard(request):
    return render(request, "videos/site_admin_dashboard.html", get_site_admin_overview())


@staff_member_required
@require_POST
def site_admin_channel_moderate(request, pk):
    channel = get_object_or_404(Channel, pk=pk)
    action = request.POST.get("action", "")
    if action not in {"suspend", "restore"}:
        return HttpResponseBadRequest("Invalid moderation action.")
    try:
        set_channel_suspended(actor=request.user, channel=channel, suspended=action == "suspend", reason=request.POST.get("reason", ""))
    except ValueError as error:
        return HttpResponseBadRequest(str(error))
    return redirect("site_admin_dashboard")


@staff_member_required
@require_POST
def site_admin_comment_moderate(request, pk):
    action = request.POST.get("action", "")
    try:
        found = moderate_site_comment(actor=request.user, comment_id=pk, action=action, reason=request.POST.get("reason", ""))
    except ValueError as error:
        return HttpResponseBadRequest(str(error))
    if not found: raise Http404("Comment not found")
    return redirect("site_admin_dashboard")


@staff_member_required
@require_POST
def site_admin_video_moderate(request, pk):
    video = get_object_or_404(Video, pk=pk); action = request.POST.get("action", ""); reason = request.POST.get("reason", "")
    try:
        if action == "hide": take_down_video(actor=request.user, video=video, reason=reason)
        elif action == "restore": restore_video(actor=request.user, video=video, reason=reason)
        else: return HttpResponseBadRequest("Invalid moderation action.")
    except ValueError as error: return HttpResponseBadRequest(str(error))
    return redirect("site_admin_dashboard")


@staff_member_required
@require_POST
def site_admin_user_moderate(request, pk):
    user = get_object_or_404(User, pk=pk); action = request.POST.get("action", "")
    try:
        if action == "suspend": set_user_active(actor=request.user, user=user, active=False, reason=request.POST.get("reason", ""))
        elif action == "reactivate": set_user_active(actor=request.user, user=user, active=True, reason=request.POST.get("reason", ""))
        else: return HttpResponseBadRequest("Invalid moderation action.")
    except ValueError as error: return HttpResponseBadRequest(str(error))
    return redirect("site_admin_dashboard")


@staff_member_required
@require_POST
def site_admin_community_post_moderate(request, pk):
    post = get_object_or_404(CommunityPost, pk=pk); action = request.POST.get("action", "")
    if action not in {"hide", "restore"}: return HttpResponseBadRequest("Invalid moderation action.")
    try: set_community_post_hidden(actor=request.user, post=post, hidden=action == "hide", reason=request.POST.get("reason", ""))
    except ValueError as error: return HttpResponseBadRequest(str(error))
    return redirect("site_admin_dashboard")


@staff_member_required
@require_POST
def site_admin_community_reply_moderate(request, pk):
    reply = get_object_or_404(CommunityReply, pk=pk); action = request.POST.get("action", "")
    if action not in {"hide", "restore"}: return HttpResponseBadRequest("Invalid moderation action.")
    try: set_community_reply_hidden(actor=request.user, reply=reply, hidden=action == "hide", reason=request.POST.get("reason", ""))
    except ValueError as error: return HttpResponseBadRequest(str(error))
    return redirect("site_admin_dashboard")


@login_required
def creator_audience(request):
    channels = get_creator_audience(request.user)
    if not channels: raise Http404("No owned channels")
    return render(request, "videos/creator_audience.html", {"channel_audiences": channels})
