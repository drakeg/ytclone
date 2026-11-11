from django.db.models import Exists, OuterRef, Q

from video.models import Video
from video.shorts_models import VideoShort


PUBLICATION_FILTERS = (
    ("all", "All"),
    *Video.PublicationStatus.choices,
)
FILTER_VALUES = {value for value, unused_label in PUBLICATION_FILTERS}
BULK_PUBLICATION_STATUSES = {
    Video.PublicationStatus.DRAFT,
    Video.PublicationStatus.UNLISTED,
    Video.PublicationStatus.PUBLISHED,
}


def get_creator_videos(user, requested_status, requested_query=""):
    selected_status = requested_status if requested_status in FILTER_VALUES else "all"
    selected_query = (requested_query or "").strip()
    videos = (
        Video.objects.filter(author=user, deleted_at__isnull=True)
        .select_related("channel", "category")
        .annotate(is_short=Exists(VideoShort.objects.filter(video_id=OuterRef("pk"))))
    )
    if selected_status != "all":
        videos = videos.filter(publication_status=selected_status)
    if selected_query:
        videos = videos.filter(
            Q(title__icontains=selected_query)
            | Q(description__icontains=selected_query)
            | Q(channel__name__icontains=selected_query)
            | Q(category__name__icontains=selected_query)
        )
    return videos.order_by("-pub_date", "-pk"), selected_status, selected_query


def bulk_update_publication(user, video_ids, publication_status):
    if publication_status not in BULK_PUBLICATION_STATUSES:
        raise ValueError("Invalid publication status.")

    try:
        normalized_ids = {int(video_id) for video_id in video_ids}
    except (TypeError, ValueError):
        raise ValueError("Invalid video selection.") from None

    return Video.objects.filter(
        author=user,
        pk__in=normalized_ids,
        deleted_at__isnull=True,
        moderation_state__isnull=True,
    ).update(
        publication_status=publication_status,
        publish_at=None,
    )
