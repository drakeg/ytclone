def unread_notifications(request):
    count = 0
    if request.user.is_authenticated:
        count = request.user.notifications.filter(read_at__isnull=True).count()
    return {"unread_notification_count": count}
