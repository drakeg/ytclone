from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notification


NOTIFICATION_PAGE_SIZE = 24


@login_required
def notification_list(request):
    notifications = request.user.notifications.select_related(
        "actor", "video", "channel"
    )
    page = Paginator(notifications, NOTIFICATION_PAGE_SIZE).get_page(
        request.GET.get("page")
    )
    return render(
        request,
        "videos/notification_list.html",
        {"notifications": page},
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

    page = request.POST.get("page")
    if page:
        return redirect(f"{reverse('notification_list')}?page={page}")
    return redirect("notification_list")


@login_required
@require_POST
def notification_mark_all_read(request):
    request.user.notifications.filter(read_at__isnull=True).update(
        read_at=timezone.now()
    )
    return redirect("notification_list")
