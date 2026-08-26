from django.db import models


class VideoQuestion(models.Model):
    comment = models.OneToOneField(
        "video.Comment", on_delete=models.CASCADE, related_name="question"
    )
    featured_reply = models.ForeignKey(
        "video.Comment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="featured_as_video_answer",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question: {self.comment_id}"
