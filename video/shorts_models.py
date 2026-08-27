from django.db import models


class VideoShort(models.Model):
    video = models.OneToOneField(
        "video.Video",
        on_delete=models.CASCADE,
        related_name="short_metadata",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Reserved for the later create-from-long-form workflow. Keeping Shorts as
    # normal Video rows lets all existing visibility/moderation/monetization rules
    # continue to apply without a second content authorization system.
    source_video = models.ForeignKey(
        "video.Video",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="derived_shorts",
    )
    source_start_seconds = models.PositiveIntegerField(null=True, blank=True)
    source_end_seconds = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Short: {self.video}"
