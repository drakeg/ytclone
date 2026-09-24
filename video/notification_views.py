from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notification


NOTIFICATION_PAGE_SIZE = 24
NOTIFICATION_FILTER_ALL = "all"
NOTIFICATION_FILTER_UNREAD = "unread"
NOTIFICATION_FILTERS = {NOTIFICATION_FILTER_ALL, NOTIFICATION_FILTER_UNREAD}
NOTIFICATION_KINDS = {value for value, _label in Notification.Kind.choices}
NOTIFICATION_DATE_ANY = "any"
NOTIFICATION_DATE_FILTERS = {
    NOTIFICATION_DATE_ANY: None,
    "today": 1,
    "7d": 7,
    "30d": 30,
}


def _notification_filter(value):
    if value in NOTIFICATION_FILTERS:
        return value
    return NOTIFICATION_FILTER_ALL


def _notification_kind(value):
    if value in NOTIFICATION_KINDS:
        return value
    return ""


def _notification_date(value):
    if value in NOTIFICATION_DATE_FILTERS:
        return value
    return NOTIFICATION_DATE_ANY


def _notification_list_url(
    *,
    page=None,
    notification_filter=NOTIFICATION_FILTER_ALL,
    notification_kind="",
    notification_date=NOTIFICATION_DATE_ANY,
    notification_query="",
):
    params = {}
    if notification_filter != NOTIFICATION_FILTER_ALL:
        params["filter"] = notification_filter
    if notification_kind:
        params["kind"] = notification_kind
    if notification_date != NOTIFICATION_DATE_ANY:
        params["date"] = notification_date
    if notification_query:
        params["q"] = notification_query
    if page:
        params["page"] = page
    url = reverse("notification_list")
    if params:
        return f"{url}?{urlencode(params)}"
    return url


@login_required
def notification_list(request):
    selected_filter = _notification_filter(request.GET.get("filter"))
    selected_kind = _notification_kind(request.GET.get("kind"))
    selected_date = _notification_date(request.GET.get("date"))
    query = request.GET.get("q", "").strip()
    notifications = request.user.notifications.select_related(
        "actor", "video", "channel"
    )
    if selected_filter == NOTIFICATION_FILTER_UNREAD:
        notifications = notifications.filter(read_at__isnull=True)
    if selected_kind:
        notifications = notifications.filter(kind=selected_kind)
    if query:
        notifications = notifications.filter(
            Q(actor__username__icontains=query)
            | Q(actor__first_name__icontains=query)
            | Q(actor__last_name__icontains=query)
            | Q(video__title__icontains=query)
            | Q(channel__name__icontains=query)
        )
    days = NOTIFICATION_DATE_FILTERS[selected_date]
    if days is not None:
        cutoff = timezone.now() - timezone.timedelta(days=days)
        notifications = notifications.filter(created_at__gte=cutoff)

    page = Paginator(notifications, NOTIFICATION_PAGE_SIZE).get_page(
        request.GET.get("page")
    )
    return render(
        request,
        "videos/notification_list.html",
        {
            "notifications": page,
            "notification_filter": selected_filter,
            "notification_kind": selected_kind,
            "notification_kind_choices": Notification.Kind.choices,
            "notification_date": selected_date,
            "notification_query": query,
        },
    )


@login_required
@require_POST
def notification_mark_read(request, pk):
    notification = get_object_or_404(
        Notification, pk=pk, recipient=request.user
    )
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])

    return redirect(
        _notification_list_url(
            page=request.POST.get("page"),
            notification_filter=_notification_filter(request.POST.get("filter")),
            notification_kind=_notification_kind(request.POST.get("kind")),
            notification_date=_notification_date(request.POST.get("date")),
            notification_query=request.POST.get("q", "").strip(),
        )
    )


@login_required
@require_POST
def notification_mark_all_read(request):
    request.user.notifications.filter(read_at__isnull=True).update(
        read_at=timezone.now()
    )
    return redirect("notification_list")
