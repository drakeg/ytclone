from django import forms

from .community_models import CommunityPost, CommunityReply


class CommunityPostForm(forms.ModelForm):
    poll_option_1 = forms.CharField(required=False, max_length=240, label="Poll option 1")
    poll_option_2 = forms.CharField(required=False, max_length=240, label="Poll option 2")
    poll_option_3 = forms.CharField(required=False, max_length=240, label="Poll option 3")
    poll_option_4 = forms.CharField(required=False, max_length=240, label="Poll option 4")

    class Meta:
        model = CommunityPost
        fields = ["kind", "body"]
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Share an update, ask your community a question, or start a poll…",
                }
            )
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("kind") == CommunityPost.Kind.POLL:
            options = [
                cleaned.get(f"poll_option_{number}", "").strip()
                for number in range(1, 5)
            ]
            options = [option for option in options if option]
            if len(options) < 2:
                raise forms.ValidationError("Polls need at least two options.")
            cleaned["poll_options"] = options
        else:
            cleaned["poll_options"] = []
        return cleaned


class CommunityReplyForm(forms.ModelForm):
    class Meta:
        model = CommunityReply
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 2, "placeholder": "Join the conversation…"}
            )
        }
