from django import forms

from .community_models import CommunityPost, CommunityReply


class CommunityPostForm(forms.ModelForm):
    class Meta:
        model = CommunityPost
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Share an update, ask your community a question, or start a conversation…",
                }
            )
        }


class CommunityReplyForm(forms.ModelForm):
    class Meta:
        model = CommunityReply
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 2, "placeholder": "Join the conversation…"}
            )
        }
