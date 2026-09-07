from django.db.models import Count

from video.models import Video


VIDEO_BROWSE_SORTS = {
    "newest": "Newest",
    "views": "Most viewed",
    "likes": "Most liked",
}


def browse_videos(user, sort="newest"):
    selected_sort = sort if sort in VIDEO_BROWSE_SORTS else "newest"
    videos = (
        Video.objects.visible_to(user)
        .filter(short_metadata__isnull=True)
        .select_related("author", "channel", "category")
        .prefetch_related("hashtags")
    )

    if selected_sort == "views":
        videos = videos.order_by("-views", "-pub_date", "-pk")
    elif selected_sort == "likes":
        videos = videos.annotate(like_count=Count("likes", distinct=True)).order_by(
            "-like_count", "-views", "-pub_date", "-pk"
        )
    else:
        videos = videos.order_by("-pub_date", "-pk")

    return videos, selected_sort
