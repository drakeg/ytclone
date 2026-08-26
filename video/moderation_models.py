from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver


class VideoModerationState(models.Model):
    video = models.OneToOneField(
        "video.Video", on_delete=models.CASCADE, related_name="moderation_state"
    )
    original_publication_status = models.CharField(max_length=12)
    original_publish_at = models.DateTimeField(null=True, blank=True)
    hidden_at = models.DateTimeField(auto_now_add=True)


class CommunityPostModerationState(models.Model):
    post = models.OneToOneField(
        "video.CommunityPost", on_delete=models.CASCADE, related_name="moderation_state"
    )
    hidden_at = models.DateTimeField(auto_now_add=True)


class CommunityReplyModerationState(models.Model):
    reply = models.OneToOneField(
        "video.CommunityReply", on_delete=models.CASCADE, related_name="moderation_state"
    )
    hidden_at = models.DateTimeField(auto_now_add=True)


class ModerationAuditEvent(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="moderation_audit_events",
    )
    action = models.CharField(max_length=40)
    target_type = models.CharField(max_length=40)
    target_id = models.PositiveBigIntegerField()
    reason = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"{self.actor}: {self.action} {self.target_type}#{self.target_id}"


@receiver(pre_save, sender="video.Video")
def keep_moderated_video_private(sender, instance, **kwargs):
    if instance.pk and VideoModerationState.objects.filter(video_id=instance.pk).exists():
        instance.publication_status = "draft"
        instance.publish_at = None
