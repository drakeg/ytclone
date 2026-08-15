from video.models import Comment


COMMENT_FILTERS = (
    ("all", "All"),
    ("visible", "Visible"),
    ("hidden", "Hidden"),
)
FILTER_VALUES = {value for value, unused_label in COMMENT_FILTERS}
BULK_ACTIONS = {
    "hide": True,
    "restore": False,
}


def get_creator_comments(user, requested_filter):
    selected_filter = (
        requested_filter if requested_filter in FILTER_VALUES else "all"
    )
    comments = Comment.objects.filter(
        video__author=user,
        video__deleted_at__isnull=True,
    ).select_related("author", "video", "video__channel")
    if selected_filter == "visible":
        comments = comments.filter(is_hidden=False)
    elif selected_filter == "hidden":
        comments = comments.filter(is_hidden=True)
    return comments.order_by("-pub_date", "-pk"), selected_filter


def bulk_moderate_comments(user, comment_ids, action):
    if action not in BULK_ACTIONS:
        raise ValueError("Invalid moderation action.")
    try:
        normalized_ids = {int(comment_id) for comment_id in comment_ids}
    except (TypeError, ValueError):
        raise ValueError("Invalid comment selection.") from None

    return Comment.objects.filter(
        pk__in=normalized_ids,
        video__author=user,
        video__deleted_at__isnull=True,
    ).update(is_hidden=BULK_ACTIONS[action])
