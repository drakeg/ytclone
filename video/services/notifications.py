from video.models import Notification
from django.utils import timezone


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


def notify_new_upload(video):
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
