from .services.channels import accessible_channels


def unread_notifications(request):
    count = 0
    is_creator = False
    if request.user.is_authenticated:
        count = request.user.notifications.filter(read_at__isnull=True).count()
        is_creator = accessible_channels(request.user).exists()
    return {
        "unread_notification_count": count,
        "is_creator": is_creator,
    }
