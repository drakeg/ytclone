from datetime import timedelta

from django.utils import timezone

from video.models import Video


TRASH_RETENTION = timedelta(days=30)


def get_creator_trash(user):
    return (
        Video.objects.filter(author=user, deleted_at__isnull=False)
        .select_related("channel", "category")
        .order_by("-deleted_at", "-pk")
    )


def trash_video(video):
    video.deleted_at = timezone.now()
    video.publication_status = Video.PublicationStatus.DRAFT
    video.publish_at = None
    video.save(update_fields=["deleted_at", "publication_status", "publish_at"])


def restore_video(video):
    video.deleted_at = None
    video.publication_status = Video.PublicationStatus.DRAFT
    video.publish_at = None
    video.save(update_fields=["deleted_at", "publication_status", "publish_at"])


def permanent_deletion_available_at(video):
    if video.deleted_at is None:
        return None
    return video.deleted_at + TRASH_RETENTION


def can_permanently_delete(video, now=None):
    available_at = permanent_deletion_available_at(video)
    return available_at is not None and (now or timezone.now()) >= available_at


def permanently_delete_video(video):
    if not can_permanently_delete(video):
        raise ValueError("This video is still within its retention period.")
    video.delete()
