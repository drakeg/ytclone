from django.shortcuts import get_object_or_404, render

from .metadata_models import Hashtag
from .models import Video


def hashtag_detail(request, name):
    hashtag = get_object_or_404(Hashtag, name=name.lower())
    videos = (
        Video.objects.visible_to(request.user)
        .filter(hashtags=hashtag)
        .select_related("author", "channel", "category")
        .order_by("-pub_date", "-pk")
    )
    return render(
        request,
        "videos/hashtag_detail.html",
        {"hashtag": hashtag, "videos": videos},
    )
