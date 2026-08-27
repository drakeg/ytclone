from video.models import Video


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


def get_creator_videos(user, requested_status):
    selected_status = requested_status if requested_status in FILTER_VALUES else "all"
    videos = Video.objects.filter(
        author=user, deleted_at__isnull=True
    ).select_related("channel", "category")
    if selected_status != "all":
        videos = videos.filter(publication_status=selected_status)
    return videos.order_by("-pub_date", "-pk"), selected_status


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
