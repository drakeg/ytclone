from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Channel, Comment, Playlist, Video


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["comment"]


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


class PlaylistForm(forms.ModelForm):
    class Meta:
        model = Playlist
        fields = ["name", "description", "visibility"]


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
        fields = ["title", "description", "thumbnail", "video_file", "category", "channel", "publication_status", "publish_at"]
        widgets = {
            "thumbnail": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp"}
            ),
            "video_file": forms.ClearableFileInput(
                attrs={"accept": "video/mp4,video/webm,video/quicktime"}
            ),
            "publish_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["channel"].queryset = (
            Channel.objects.filter(owner=user) if user else Channel.objects.none()
        )
        self.fields["channel"].required = True
        if user and not self.fields["channel"].queryset.exists():
            self.fields["channel"].help_text = "Create a channel before uploading a video."

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("publication_status")
        publish_at = cleaned_data.get("publish_at")
        if status == Video.PublicationStatus.SCHEDULED:
            if publish_at is None:
                self.add_error("publish_at", "Choose a publication time.")
            elif publish_at <= timezone.now():
                self.add_error("publish_at", "Choose a future publication time.")
        else:
            cleaned_data["publish_at"] = None
        return cleaned_data

    def clean_thumbnail(self):
        thumbnail = self.cleaned_data.get("thumbnail")
        if not thumbnail:
            return thumbnail
        if not hasattr(thumbnail, "content_type"):
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
        if not hasattr(video_file, "content_type"):
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


class VideoEditForm(VideoUploadForm):
    class Meta(VideoUploadForm.Meta):
        fields = ["title", "description", "thumbnail", "video_file", "category", "channel", "publication_status", "publish_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["thumbnail"].required = False
        self.fields["video_file"].required = False
