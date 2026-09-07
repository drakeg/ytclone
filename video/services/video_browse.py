from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from video.models import Category, Video


VIDEO_BROWSE_SORTS = {
    "newest": "Newest",
    "views": "Most viewed",
    "likes": "Most liked",
}

VIDEO_BROWSE_UPLOAD_FILTERS = {
    "any": "Any time",
    "today": "Today",
    "week": "This week",
    "month": "This month",
    "year": "This year",
}


def normalize_browse_category(category):
    if isinstance(category, Category):
        return category
    try:
        category_id = int(category)
    except (TypeError, ValueError):
        return None
    if category_id <= 0:
        return None
    return Category.objects.filter(pk=category_id).first()


def normalize_browse_upload(uploaded):
    return uploaded if uploaded in VIDEO_BROWSE_UPLOAD_FILTERS else "any"


def _upload_date_start(uploaded):
    if uploaded == "any":
        return None

    now = timezone.localtime(timezone.now())
    if uploaded == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if uploaded == "week":
        return now - timedelta(days=7)
    if uploaded == "month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if uploaded == "year":
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return None


def browse_videos(user, sort="newest", category=None, uploaded="any"):
    selected_sort = sort if sort in VIDEO_BROWSE_SORTS else "newest"
    selected_category = normalize_browse_category(category)
    selected_upload = normalize_browse_upload(uploaded)

    videos = (
        Video.objects.visible_to(user)
        .filter(short_metadata__isnull=True)
        .select_related("author", "channel", "category")
        .prefetch_related("hashtags")
    )

    if selected_category is not None:
        videos = videos.filter(category=selected_category)

    upload_date_start = _upload_date_start(selected_upload)
    if upload_date_start is not None:
        videos = videos.filter(pub_date__gte=upload_date_start)

    if selected_sort == "views":
        videos = videos.order_by("-views", "-pub_date", "-pk")
    elif selected_sort == "likes":
        videos = videos.annotate(like_count=Count("likes", distinct=True)).order_by(
            "-like_count", "-views", "-pub_date", "-pk"
        )
    else:
        videos = videos.order_by("-pub_date", "-pk")

    return videos, selected_sort
