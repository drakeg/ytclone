from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.static import serve

from . import views
from .models import Video


AUTHORIZED_SHARED_MEDIA_SESSION_KEY = "authorized_shared_video_media_ids"


def shared_video_detail(request, token):
    video = get_object_or_404(
        Video.objects.select_related("author", "channel", "category"),
        share_token=token,
        publication_status=Video.PublicationStatus.UNLISTED,
        deleted_at__isnull=True,
    )
    if not video.has_member_access(request.user):
        raise Http404("Video not found")

    authorized_ids = request.session.get(AUTHORIZED_SHARED_MEDIA_SESSION_KEY, [])
    if video.pk not in authorized_ids:
        authorized_ids.append(video.pk)
        request.session[AUTHORIZED_SHARED_MEDIA_SESSION_KEY] = authorized_ids[-50:]

    return views._render_video_detail(request, video)


def media_video_file(request, path):
    storage_name = f"videos/files/{path}"
    video = get_object_or_404(
        Video.objects.select_related("channel"),
        video_file=storage_name,
        deleted_at__isnull=True,
    )
    authorized_shared_ids = request.session.get(AUTHORIZED_SHARED_MEDIA_SESSION_KEY, [])
    if not video.is_visible_to(request.user) and video.pk not in authorized_shared_ids:
        raise Http404("Video not found")

    if settings.USE_S3_MEDIA:
        return redirect(video.video_file.url)
    return serve(request, storage_name, document_root=settings.MEDIA_ROOT)
