from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .services.administration import (
    get_creator_audience,
    get_site_admin_overview,
    moderate_site_comment,
)


@staff_member_required
def site_admin_dashboard(request):
    return render(
        request,
        "videos/site_admin_dashboard.html",
        get_site_admin_overview(),
    )


@staff_member_required
@require_POST
def site_admin_comment_moderate(request, pk):
    action = request.POST.get("action", "")
    try:
        found = moderate_site_comment(comment_id=pk, action=action)
    except ValueError as error:
        return HttpResponseBadRequest(str(error))
    if not found:
        raise Http404("Comment not found")
    return redirect("site_admin_dashboard")


@login_required
def creator_audience(request):
    channels = get_creator_audience(request.user)
    if not channels:
        raise Http404("No owned channels")
    return render(
        request,
        "videos/creator_audience.html",
        {"channel_audiences": channels},
    )
