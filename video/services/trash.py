from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from video.models import Video


TRASH_RETENTION = timedelta(days=30)


def get_creator_trash(user, requested_query=""):
    selected_query = (requested_query or "").strip()
    videos = (
        Video.objects.filter(author=user, deleted_at__isnull=False)
        .select_related("channel", "category")
    )
    if selected_query:
        videos = videos.filter(
            Q(title__icontains=selected_query)
            | Q(description__icontains=selected_query)
            | Q(channel__name__icontains=selected_query)
            | Q(category__name__icontains=selected_query)
        )
    return videos.order_by("-deleted_at", "-pk"), selected_query


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
