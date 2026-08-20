from django.conf import settings
from django.db import models


class CommunityPost(models.Model):
    class Kind(models.TextChoices):
        UPDATE = "update", "Update"
        QUESTION = "question", "Question"
        POLL = "poll", "Poll"

    channel = models.ForeignKey(
        "video.Channel", on_delete=models.CASCADE, related_name="community_posts"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
    )
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.UPDATE)
    body = models.TextField(max_length=5000)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_community_posts",
        blank=True,
    )
    featured_reply = models.ForeignKey(
        "CommunityReply",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="featured_on_posts",
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


class CommunityPollOption(models.Model):
    post = models.ForeignKey(
        CommunityPost, on_delete=models.CASCADE, related_name="poll_options"
    )
    text = models.CharField(max_length=240)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "pk"]

    def __str__(self):
        return self.text


class CommunityPollVote(models.Model):
    post = models.ForeignKey(
        CommunityPost, on_delete=models.CASCADE, related_name="poll_votes"
    )
    option = models.ForeignKey(
        CommunityPollOption, on_delete=models.CASCADE, related_name="votes"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_poll_votes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "user"], name="unique_user_per_community_poll"
            )
        ]

    def __str__(self):
        return f"{self.user} -> {self.option}"
