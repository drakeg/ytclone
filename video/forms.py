from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib.auth.models import User

from .models import Comment, Video


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["comment"]


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


class VideoUploadForm(forms.ModelForm):
    allowed_video_extensions = {".mp4", ".webm", ".mov"}
    allowed_video_content_types = {
        "video/mp4",
        "video/webm",
        "video/quicktime",
    }
    allowed_thumbnail_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    allowed_thumbnail_content_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    class Meta:
        model = Video
        fields = ["title", "description", "thumbnail", "video_file", "category"]
        widgets = {
            "thumbnail": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp"}
            ),
            "video_file": forms.ClearableFileInput(
                attrs={"accept": "video/mp4,video/webm,video/quicktime"}
            ),
        }

    def clean_thumbnail(self):
        thumbnail = self.cleaned_data.get("thumbnail")
        if not thumbnail:
            return thumbnail

        extension = Path(thumbnail.name).suffix.lower()
        content_type = getattr(thumbnail, "content_type", "").lower()

        if extension not in self.allowed_thumbnail_extensions:
            raise forms.ValidationError("Use a JPG, PNG, or WebP thumbnail.")
        if content_type and content_type not in self.allowed_thumbnail_content_types:
            raise forms.ValidationError("The thumbnail file type is not supported.")
        if thumbnail.size > settings.MAX_THUMBNAIL_UPLOAD_SIZE:
            raise forms.ValidationError(
                f"Thumbnail files must be {settings.MAX_THUMBNAIL_UPLOAD_MB} MB or smaller."
            )

        return thumbnail

    def clean_video_file(self):
        video_file = self.cleaned_data.get("video_file")
        if not video_file:
            return video_file

        extension = Path(video_file.name).suffix.lower()
        content_type = getattr(video_file, "content_type", "").lower()

        if extension not in self.allowed_video_extensions:
            raise forms.ValidationError("Use an MP4, WebM, or MOV video file.")
        if content_type and content_type not in self.allowed_video_content_types:
            raise forms.ValidationError("The video file type is not supported.")
        if video_file.size > settings.MAX_VIDEO_UPLOAD_SIZE:
            raise forms.ValidationError(
                f"Video files must be {settings.MAX_VIDEO_UPLOAD_MB} MB or smaller."
            )

        return video_file
