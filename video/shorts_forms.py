from django import forms

from .shorts_models import VideoShort


class ShortClipForm(forms.Form):
    title = forms.CharField(max_length=255)
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}))
    start_seconds = forms.IntegerField(min_value=0, help_text="Start time in seconds.")
    end_seconds = forms.IntegerField(min_value=1, help_text="End time in seconds. Maximum clip length is 180 seconds.")
    reframing_mode = forms.ChoiceField(
        choices=VideoShort.ReframingMode.choices,
        required=False,
        initial=VideoShort.ReframingMode.VERTICAL_CENTER,
        help_text="Choose how the source frame should fit a Short. Vertical options render at 720×1280.",
    )
    overlay_text = forms.CharField(
        required=False,
        max_length=120,
        help_text="Optional text burned into the Short. Maximum 120 characters.",
    )
    overlay_position = forms.ChoiceField(
        choices=VideoShort.OverlayPosition.choices,
        required=False,
        initial=VideoShort.OverlayPosition.BOTTOM,
        help_text="Choose where the optional text appears.",
    )

    def clean_reframing_mode(self):
        return self.cleaned_data.get("reframing_mode") or VideoShort.ReframingMode.ORIGINAL

    def clean_overlay_text(self):
        return (self.cleaned_data.get("overlay_text") or "").strip()

    def clean_overlay_position(self):
        return self.cleaned_data.get("overlay_position") or VideoShort.OverlayPosition.BOTTOM

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_seconds")
        end = cleaned.get("end_seconds")
        if start is None or end is None:
            return cleaned
        if end <= start:
            self.add_error("end_seconds", "End time must be after the start time.")
        elif end - start > 180:
            self.add_error("end_seconds", "Short clips must be 180 seconds or shorter.")
        return cleaned
