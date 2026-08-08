from video.models import Notification


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
