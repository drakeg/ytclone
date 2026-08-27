from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Channel, Comment, Playlist, Video
from .services.channels import accessible_channels
from .services.chapters import ChapterValidationError, format_chapters, parse_chapters
from .services.metadata import normalize_tag_names


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
    content_format = forms.ChoiceField(
        required=False,
        choices=(("video", "Standard video"), ("short", "Short")),
        initial="video",
        help_text="Choose Short for short-form vertical-style content. This does not crop or transcode the file.",
    )
    tags = forms.CharField(
        required=False,
        help_text="Optional. Separate tags with commas, for example: rv travel, camping, solar.",
        widget=forms.TextInput(attrs={"placeholder": "rv travel, camping, solar"}),
    )
    chapters = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 6, "placeholder": "0:00 Introduction\n1:30 Main topic"}), help_text="Optional. One line per chapter: MM:SS Title or HH:MM:SS Title.")
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
        fields = [
            "title",
            "description",
            "thumbnail",
            "video_file",
            "category",
            "channel",
            "publication_status",
            "audience",
            "publish_at",
            "public_release_at",
        ]
        widgets = {
            "thumbnail": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp"}
            ),
            # Do not set an ``accept`` filter on the video chooser. Chrome on macOS
            # can spend a very long time filtering large/mixed folders before the
            # native picker becomes responsive. Server-side validation below still
            # enforces the supported extensions, MIME types, and upload-size limit.
            "video_file": forms.ClearableFileInput(),
            "publish_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "public_release_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["channel"].queryset = accessible_channels(user)
        self.fields["channel"].required = True
        self.fields["audience"].required = False
        self.fields["audience"].initial = Video.Audience.EVERYONE
        self.fields["audience"].help_text = (
            "Paid members only requires an active paid membership for the selected channel."
        )
        self.fields["public_release_at"].required = False
        self.fields["public_release_at"].help_text = (
            "Optional for paid-members-only videos. Members can watch first; everyone gets access automatically at this time."
        )
        if user and not self.fields["channel"].queryset.exists():
            self.fields["channel"].help_text = "Create a channel before uploading a video."
        if self.instance and self.instance.pk:
            self.fields["chapters"].initial = format_chapters(self.instance)
            self.fields["tags"].initial = ", ".join(
                self.instance.tags.values_list("name", flat=True)
            )
            self.fields["content_format"].initial = (
                "short" if hasattr(self.instance, "short_metadata") else "video"
            )

    def clean_tags(self):
        try:
            return normalize_tag_names(self.cleaned_data.get("tags", ""))
        except ValueError as error:
            raise forms.ValidationError(str(error))

    def clean_chapters(self):
        try:
            return parse_chapters(self.cleaned_data.get("chapters", ""))
        except ChapterValidationError as error:
            raise forms.ValidationError(str(error))

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("publication_status")
        publish_at = cleaned_data.get("publish_at")
        public_release_at = cleaned_data.get("public_release_at")
        audience = cleaned_data.get("audience") or Video.Audience.EVERYONE
        cleaned_data["audience"] = audience
        channel = cleaned_data.get("channel")

        if audience == Video.Audience.MEMBERS_ONLY and channel is not None:
            from monetization.models import CreatorMonetizationAccount

            if not CreatorMonetizationAccount.objects.filter(
                channel=channel,
                status=CreatorMonetizationAccount.Status.ACTIVE,
                payouts_enabled=True,
                terms_accepted_at__isnull=False,
            ).exists():
                self.add_error(
                    "audience",
                    "Enable monetization for this channel before publishing members-only videos.",
                )

        if audience == Video.Audience.EVERYONE:
            cleaned_data["public_release_at"] = None
            if public_release_at is not None:
                self.add_error(
                    "public_release_at",
                    "Public release timing is only available for paid-members-only videos.",
                )
        elif public_release_at is not None and public_release_at <= timezone.now():
            self.add_error(
                "public_release_at",
                "Choose a future public release time, or leave it blank to keep the video members only.",
            )

        if status == Video.PublicationStatus.SCHEDULED:
            if publish_at is None:
                self.add_error("publish_at", "Choose a publication time.")
            elif publish_at <= timezone.now():
                self.add_error("publish_at", "Choose a future publication time.")
            elif public_release_at is not None and public_release_at <= publish_at:
                self.add_error(
                    "public_release_at",
                    "Public release must be after the scheduled member publication time.",
                )
        else:
            cleaned_data["publish_at"] = None
        return cleaned_data

    def save(self, commit=True):
        self.instance._pending_tag_names = self.cleaned_data.get("tags", [])
        requested_format = self.cleaned_data.get("content_format")
        if requested_format:
            self.instance._pending_short_state = requested_format == "short"
        elif not self.instance.pk:
            self.instance._pending_short_state = False
        return super().save(commit=commit)

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
        fields = [
            "title",
            "description",
            "thumbnail",
            "video_file",
            "category",
            "channel",
            "publication_status",
            "audience",
            "publish_at",
            "public_release_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["thumbnail"].required = False
        self.fields["video_file"].required = False
