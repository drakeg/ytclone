from django.utils import timezone

from .services.channels import accessible_channels
from .services.notifications import deliver_due_scheduled_upload_notifications


def unread_notifications(request):
    # Scheduled publishing is request-time based, so use the same low-cost model
    # for in-app upload notifications. The service is idempotent and bounded;
    # the management command remains available for deterministic catch-up.
    deliver_due_scheduled_upload_notifications(limit=10)

    count = 0
    is_creator = False
    pending_team_invitation_count = 0
    if request.user.is_authenticated:
        count = request.user.notifications.filter(read_at__isnull=True).count()
        is_creator = accessible_channels(request.user).exists()
        pending_team_invitation_count = request.user.channel_team_invitations.filter(
            status="pending", expires_at__gt=timezone.now()
        ).count()
    return {
        "unread_notification_count": count,
        "is_creator": is_creator,
        "pending_team_invitation_count": pending_team_invitation_count,
    }
