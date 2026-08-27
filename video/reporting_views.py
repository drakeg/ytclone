from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .reporting_forms import ContentReportForm, ContentReportReviewForm
from .reporting_models import ContentReport
from .services.reporting import (
    create_report,
    get_reportable_target,
    report_queue,
    review_report,
)


@login_required
def report_content(request, target_type, target_id):
    try:
        target = get_reportable_target(request.user, target_type, target_id)
    except ValueError as error:
        return HttpResponseBadRequest(str(error))
    if target is None:
        raise Http404("Report target not found")

    if request.method == "POST":
        form = ContentReportForm(request.POST)
        if form.is_valid():
            report, created = create_report(
                reporter=request.user,
                target=target,
                reason=form.cleaned_data["reason"],
                details=form.cleaned_data["details"],
            )
            if created:
                messages.success(request, "Report submitted for site staff review.")
            else:
                messages.info(request, "You already have an open report for this content.")
            return redirect(target.url)
    else:
        form = ContentReportForm()

    return render(
        request,
        "videos/content_report_form.html",
        {"form": form, "target": target},
    )


@staff_member_required
def site_admin_report_queue(request):
    reports, selected_status = report_queue(request.GET.get("status", "open"))
    return render(
        request,
        "videos/site_admin_report_queue.html",
        {
            "reports": reports,
            "selected_status": selected_status,
            "status_options": ContentReport.Status.choices,
        },
    )


@staff_member_required
@require_POST
def site_admin_report_review(request, pk):
    report = get_object_or_404(ContentReport, pk=pk)
    form = ContentReportReviewForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest("A valid action and resolution note are required.")
    try:
        review_report(
            report=report,
            reviewer=request.user,
            action=form.cleaned_data["action"],
            resolution_note=form.cleaned_data["resolution_note"],
        )
    except ValueError as error:
        return HttpResponseBadRequest(str(error))
    return redirect("site_admin_report_queue")
