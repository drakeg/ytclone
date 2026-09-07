from django.db.models import Case, IntegerField, Q, Value, When

from ..models import Video


WATCH_RECOMMENDATION_LIMIT = 8


def watch_recommendations(video, user, limit=WATCH_RECOMMENDATION_LIMIT):
    """Return a small deterministic set of visible long-form videos to watch next."""
    limit = max(0, min(int(limit), WATCH_RECOMMENDATION_LIMIT))
    if limit == 0:
        return Video.objects.none()

    candidates = (
        Video.objects.visible_to(user)
        .filter(short_metadata__isnull=True)
        .exclude(pk=video.pk)
        .select_related("author", "channel", "category")
    )

    same_category = Q(pk__isnull=True)
    if video.category_id:
        same_category = Q(category_id=video.category_id)

    same_channel = Q(pk__isnull=True)
    if video.channel_id:
        same_channel = Q(channel_id=video.channel_id)

    candidates = candidates.annotate(
        recommendation_rank=Case(
            When(same_category, then=Value(0)),
            When(same_channel, then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by("recommendation_rank", "-pub_date", "-pk")

    return candidates[:limit]
