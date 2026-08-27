from django.shortcuts import render

from .models import Video


def shorts_feed(request):
    shorts = (
        Video.objects.visible_to(request.user)
        .filter(short_metadata__isnull=False)
        .select_related("author", "channel", "category")
        .prefetch_related("likes", "dislikes", "tags", "hashtags")
        .order_by("-pub_date", "-pk")[:50]
    )
    return render(request, "videos/shorts_feed.html", {"shorts": shorts})
