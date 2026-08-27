from django import forms


class ShortClipForm(forms.Form):
    title = forms.CharField(max_length=255)
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}))
    start_seconds = forms.IntegerField(min_value=0, help_text="Start time in seconds.")
    end_seconds = forms.IntegerField(min_value=1, help_text="End time in seconds. Maximum clip length is 180 seconds.")

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
