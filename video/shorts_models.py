from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class VideoShort(models.Model):
    class ReframingMode(models.TextChoices):
        ORIGINAL = "original", "Keep original frame"
        VERTICAL_LEFT = "vertical_left", "Vertical 9:16 — focus left"
        VERTICAL_CENTER = "vertical_center", "Vertical 9:16 — focus center"
        VERTICAL_RIGHT = "vertical_right", "Vertical 9:16 — focus right"

    video = models.OneToOneField(
        "video.Video",
        on_delete=models.CASCADE,
        related_name="short_metadata",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Source linkage supports creator-generated Shorts without introducing a
    # second content authorization system.
    source_video = models.ForeignKey(
        "video.Video",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="derived_shorts",
    )
    source_start_seconds = models.PositiveIntegerField(null=True, blank=True)
    source_end_seconds = models.PositiveIntegerField(null=True, blank=True)
    reframing_mode = models.CharField(
        max_length=20,
        choices=ReframingMode.choices,
        default=ReframingMode.ORIGINAL,
    )

    def __str__(self):
        return f"Short: {self.video}"


@receiver(post_save, sender="video.Video")
def sync_short_metadata(sender, instance, **kwargs):
    desired = getattr(instance, "_pending_short_state", None)
    if desired is None:
        return
    if desired:
        VideoShort.objects.get_or_create(video=instance)
    else:
        VideoShort.objects.filter(video=instance).delete()
