from django import forms

from .reporting_models import ContentReport


class ContentReportForm(forms.Form):
    reason = forms.ChoiceField(choices=ContentReport.Reason.choices)
    details = forms.CharField(
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Optional. Add context that will help site staff review the report.",
    )


class ContentReportReviewForm(forms.Form):
    action = forms.ChoiceField(
        choices=(("resolve", "Resolve"), ("dismiss", "Dismiss"))
    )
    resolution_note = forms.CharField(
        required=True,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
