from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    videos = models.ManyToManyField("video.Video", related_name="tags", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Hashtag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    videos = models.ManyToManyField("video.Video", related_name="hashtags", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"#{self.name}"


@receiver(post_save, sender="video.Video")
def synchronize_video_metadata(sender, instance, **kwargs):
    from .services.metadata import sync_video_metadata

    pending_tags = getattr(instance, "_pending_tag_names", None)
    sync_video_metadata(instance, structured_tags=pending_tags)
    if hasattr(instance, "_pending_tag_names"):
        delattr(instance, "_pending_tag_names")
