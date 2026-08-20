from django.conf import settings
from django.db import models


class CommunityPost(models.Model):
    channel = models.ForeignKey(
        "video.Channel", on_delete=models.CASCADE, related_name="community_posts"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
    )
    body = models.TextField(max_length=5000)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_community_posts",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"{self.channel}: {self.body[:60]}"


class CommunityReply(models.Model):
    post = models.ForeignKey(
        CommunityPost, on_delete=models.CASCADE, related_name="replies"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_replies",
    )
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return f"{self.author}: {self.body[:60]}"
