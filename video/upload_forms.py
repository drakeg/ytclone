from django import forms

from .forms import VideoUploadForm


class ThumbnailVideoUploadForm(VideoUploadForm):
    THUMBNAIL_AUTO = "auto"
    THUMBNAIL_FRAME = "frame"
    THUMBNAIL_CUSTOM = "custom"

    thumbnail_mode = forms.ChoiceField(
        required=False,
        choices=(
            (THUMBNAIL_AUTO, "Automatically select a frame"),
            (THUMBNAIL_FRAME, "Choose a frame from the video"),
            (THUMBNAIL_CUSTOM, "Upload a custom thumbnail"),
        ),
        initial=THUMBNAIL_AUTO,
        widget=forms.RadioSelect,
        help_text="Every uploaded video receives a thumbnail. Choose how VideoShare should create it.",
    )
    thumbnail_frame_seconds = forms.FloatField(
        required=False,
        min_value=0,
        widget=forms.HiddenInput,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["thumbnail"].required = False

    def clean(self):
        cleaned_data = super().clean()
        thumbnail = cleaned_data.get("thumbnail")
        mode = cleaned_data.get("thumbnail_mode")
        if not mode:
            mode = self.THUMBNAIL_CUSTOM if thumbnail else self.THUMBNAIL_AUTO
        cleaned_data["thumbnail_mode"] = mode
        frame_seconds = cleaned_data.get("thumbnail_frame_seconds")

        if mode == self.THUMBNAIL_CUSTOM and not thumbnail:
            self.add_error("thumbnail", "Upload a thumbnail image when Custom thumbnail is selected.")
        if mode == self.THUMBNAIL_FRAME and frame_seconds is None:
            self.add_error(
                "thumbnail_frame_seconds",
                "Choose a frame from the video before uploading.",
            )
        return cleaned_data
