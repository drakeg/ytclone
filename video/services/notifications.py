from django.db import transaction
from django.utils import timezone

from video.models import Notification, Video


def create_notification(*, recipient, actor, kind, video=None, channel=None):
    if recipient.pk == actor.pk:
        return None
    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        kind=kind,
        video=video,
        channel=channel,
    )


def notify_comment(comment):
    return create_notification(
        recipient=comment.video.author,
        actor=comment.author,
        kind=Notification.Kind.COMMENT,
        video=comment.video,
    )


def notify_reply(reply):
    parent = reply.parent
    if parent is None or parent.author_id == reply.video.author_id:
        return None
    return create_notification(
        recipient=parent.author,
        actor=reply.author,
        kind=Notification.Kind.REPLY,
        video=reply.video,
    )


def notify_reaction(*, video, actor, kind):
    return create_notification(
        recipient=video.author,
        actor=actor,
        kind=kind,
        video=video,
    )


def notify_subscription(*, channel, actor):
    return create_notification(
        recipient=channel.owner,
        actor=actor,
        kind=Notification.Kind.SUBSCRIPTION,
        channel=channel,
    )


def _create_upload_notifications(video):
    if video.channel_id is None:
        return 0
    notifications = [
        Notification(
            recipient=subscriber,
            actor=video.author,
            kind=Notification.Kind.UPLOAD,
            video=video,
            channel=video.channel,
        )
        for subscriber in video.channel.subscribers.exclude(pk=video.author_id)
    ]
    Notification.objects.bulk_create(notifications)
    return len(notifications)


def notify_new_upload(video):
    """Deliver upload notifications once for an immediately published video."""
    with transaction.atomic():
        locked = Video.objects.select_for_update().select_related("channel", "author").get(pk=video.pk)
        if locked.upload_notifications_sent_at is not None:
            return 0
        count = _create_upload_notifications(locked)
        locked.upload_notifications_sent_at = timezone.now()
        locked.save(update_fields=["upload_notifications_sent_at"])
        video.upload_notifications_sent_at = locked.upload_notifications_sent_at
        return count


def deliver_due_scheduled_upload_notifications(*, limit=25, now=None):
    """Deliver notifications for due scheduled uploads, at most once per video."""
    now = now or timezone.now()
    due_ids = list(
        Video.objects.filter(
            publication_status=Video.PublicationStatus.SCHEDULED,
            publish_at__isnull=False,
            publish_at__lte=now,
            upload_notifications_sent_at__isnull=True,
            deleted_at__isnull=True,
        )
        .order_by("publish_at", "pk")
        .values_list("pk", flat=True)[:limit]
    )
    delivered_videos = 0
    delivered_notifications = 0
    for video_id in due_ids:
        with transaction.atomic():
            video = (
                Video.objects.select_for_update()
                .select_related("channel", "author")
                .get(pk=video_id)
            )
            if video.upload_notifications_sent_at is not None:
                continue
            if (
                video.publication_status != Video.PublicationStatus.SCHEDULED
                or video.publish_at is None
                or video.publish_at > now
                or video.deleted_at is not None
            ):
                continue
            delivered_notifications += _create_upload_notifications(video)
            video.upload_notifications_sent_at = now
            video.save(update_fields=["upload_notifications_sent_at"])
            delivered_videos += 1
    return delivered_videos, delivered_notifications


def notify_team_invitation(invitation):
    return create_notification(
        recipient=invitation.invitee,
        actor=invitation.invited_by,
        kind=Notification.Kind.TEAM_INVITATION,
        channel=invitation.channel,
    )


def clear_team_invitation_notification(invitation):
    return Notification.objects.filter(
        recipient=invitation.invitee,
        actor=invitation.invited_by,
        channel=invitation.channel,
        kind=Notification.Kind.TEAM_INVITATION,
        read_at__isnull=True,
    ).update(read_at=timezone.now())
