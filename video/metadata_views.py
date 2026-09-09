from django.shortcuts import get_object_or_404, render

from .metadata_models import Hashtag, Tag
from .models import Video


def _topic_videos(request, relation, topic):
    return (
        Video.objects.visible_to(request.user)
        .filter(**{relation: topic})
        .select_related("author", "channel", "category")
        .order_by("-pub_date", "-pk")
    )


def tag_detail(request, name):
    tag = get_object_or_404(Tag, name=name.lower())
    return render(
        request,
        "videos/tag_detail.html",
        {"tag": tag, "videos": _topic_videos(request, "tags", tag)},
    )


def hashtag_detail(request, name):
    hashtag = get_object_or_404(Hashtag, name=name.lower())
    return render(
        request,
        "videos/hashtag_detail.html",
        {"hashtag": hashtag, "videos": _topic_videos(request, "hashtags", hashtag)},
    )
