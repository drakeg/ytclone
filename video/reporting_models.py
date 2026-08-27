from django.conf import settings
from django.db import models
from django.db.models import Q


class ContentReport(models.Model):
    class TargetType(models.TextChoices):
        CHANNEL = "channel", "Channel"
        VIDEO = "video", "Video"
        COMMENT = "comment", "Video comment"
        COMMUNITY_POST = "community_post", "Community post"
        COMMUNITY_REPLY = "community_reply", "Community reply"

    class Reason(models.TextChoices):
        SPAM = "spam", "Spam or misleading"
        HARASSMENT = "harassment", "Harassment or bullying"
        HATE = "hate", "Hate or abusive content"
        VIOLENCE = "violence", "Violence or dangerous content"
        SEXUAL = "sexual", "Sexual or inappropriate content"
        PRIVACY = "privacy", "Privacy or personal information"
        COPYRIGHT = "copyright", "Copyright or intellectual property"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="content_reports",
    )
    target_type = models.CharField(max_length=24, choices=TargetType.choices)
    target_id = models.PositiveBigIntegerField()
    target_label = models.CharField(max_length=255)
    reason = models.CharField(max_length=24, choices=Reason.choices)
    details = models.TextField(max_length=1000, blank=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reviewed_content_reports",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(max_length=1000, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["reporter", "target_type", "target_id"],
                condition=Q(status="open"),
                name="unique_open_report_per_user_target",
            )
        ]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="report_status_created_idx"),
            models.Index(fields=["target_type", "target_id"], name="report_target_idx"),
        ]

    def __str__(self):
        return f"{self.reporter}: {self.target_type}#{self.target_id} ({self.status})"
