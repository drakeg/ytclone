from django.db.models import Count, Q
from django.shortcuts import render

from .models import Channel, Video


def channel_list(request):
    channels = (
        Channel.objects.select_related("owner")
        .annotate(
            subscriber_count=Count("subscribers", distinct=True),
            public_video_count=Count(
                "videos",
                filter=Q(
                    videos__deleted_at__isnull=True,
                    videos__publication_status=Video.PublicationStatus.PUBLISHED,
                    videos__audience=Video.Audience.EVERYONE,
                ),
                distinct=True,
            ),
        )
        .order_by("-subscriber_count", "name", "pk")
    )
    return render(request, "videos/channel_list.html", {"channels": channels})
