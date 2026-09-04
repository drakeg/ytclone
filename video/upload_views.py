from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import Video
from .services.chapters import replace_chapters
from .services.notifications import notify_new_upload
from .services.video_thumbnails import VideoThumbnailError, generate_thumbnail_for_upload
from .upload_forms import ThumbnailVideoUploadForm


@login_required
def upload_video(request):
    if request.method == "POST":
        form = ThumbnailVideoUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            video = form.save(commit=False)
            video.author = request.user
            mode = form.cleaned_data["thumbnail_mode"]

            if mode != ThumbnailVideoUploadForm.THUMBNAIL_CUSTOM:
                try:
                    generated_thumbnail = generate_thumbnail_for_upload(
                        form.cleaned_data["video_file"],
                        mode=mode,
                        frame_seconds=form.cleaned_data.get("thumbnail_frame_seconds"),
                    )
                except VideoThumbnailError as error:
                    form.add_error(None, str(error))
                else:
                    video.thumbnail.save(
                        generated_thumbnail.name,
                        generated_thumbnail,
                        save=False,
                    )

            if not form.non_field_errors():
                video.save()
                replace_chapters(video, form.cleaned_data["chapters"])
                if video.publication_status == Video.PublicationStatus.PUBLISHED:
                    notify_new_upload(video)
                return redirect("video_detail", pk=video.pk)
    else:
        form = ThumbnailVideoUploadForm(user=request.user)
    return render(request, "videos/upload_video.html", {"form": form})
