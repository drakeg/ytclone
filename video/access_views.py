from django.http import Http404
from django.shortcuts import get_object_or_404

from . import views
from .models import Video


def shared_video_detail(request, token):
    video = get_object_or_404(
        Video.objects.select_related("author", "channel", "category"),
        share_token=token,
        publication_status=Video.PublicationStatus.UNLISTED,
        deleted_at__isnull=True,
    )
    if not video.has_member_access(request.user):
        raise Http404("Video not found")
    return views._render_video_detail(request, video)
