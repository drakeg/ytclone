import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to="categories/thumbnails", blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class VideoQuerySet(models.QuerySet):
    def visible_to(self, user):
        publication_visibility = Q(publication_status=Video.PublicationStatus.PUBLISHED) | Q(
            publication_status=Video.PublicationStatus.SCHEDULED,
            publish_at__lte=timezone.now(),
        )
        audience_visibility = Q(audience=Video.Audience.EVERYONE)
        visibility = publication_visibility & audience_visibility

        if getattr(user, "is_authenticated", False):
            from monetization.models import ChannelMembershipSubscription

            paid_channel_ids = ChannelMembershipSubscription.objects.filter(
                subscriber=user,
                status=ChannelMembershipSubscription.Status.ACTIVE,
            ).values("tier__monetization_account__channel_id")
            visibility = publication_visibility & (
                audience_visibility | Q(channel_id__in=paid_channel_ids)
            )
            visibility |= Q(author=user)

        return self.filter(visibility, deleted_at__isnull=True).distinct()


class Video(models.Model):
    class PublicationStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        UNLISTED = "unlisted", "Unlisted"
        SCHEDULED = "scheduled", "Scheduled"
        PUBLISHED = "published", "Published"

    class Audience(models.TextChoices):
        EVERYONE = "everyone", "Everyone"
        MEMBERS_ONLY = "members", "Paid members only"

    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to="videos/thumbnails")
    video_file = models.FileField(upload_to="videos/files")
    views = models.PositiveIntegerField(default=0)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.ForeignKey(
        "Channel", on_delete=models.SET_NULL, null=True, blank=True, related_name="videos"
    )
    likes = models.ManyToManyField(User, related_name="likes", blank=True)
    dislikes = models.ManyToManyField(User, related_name="dislikes", blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )
    pub_date = models.DateTimeField(auto_now_add=True)
    publication_status = models.CharField(
        max_length=12,
        choices=PublicationStatus.choices,
        default=PublicationStatus.PUBLISHED,
    )
    audience = models.CharField(
        max_length=12,
        choices=Audience.choices,
        default=Audience.EVERYONE,
    )
    publish_at = models.DateTimeField(null=True, blank=True)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = VideoQuerySet.as_manager()

    def has_member_access(self, user):
        if self.audience == self.Audience.EVERYONE:
            return True
        if not getattr(user, "is_authenticated", False):
            return False
        if self.author_id == user.pk or (self.channel_id and self.channel.owner_id == user.pk):
            return True
        if not self.channel_id:
            return False

        from monetization.models import ChannelMembershipSubscription

        return ChannelMembershipSubscription.objects.filter(
            subscriber=user,
            status=ChannelMembershipSubscription.Status.ACTIVE,
            tier__monetization_account__channel_id=self.channel_id,
        ).exists()

    def is_visible_to(self, user):
        if self.deleted_at is not None:
            return False
        if self.author_id == getattr(user, "pk", None):
            return True
        publication_visible = self.publication_status == self.PublicationStatus.PUBLISHED or (
            self.publication_status == self.PublicationStatus.SCHEDULED
            and self.publish_at is not None
            and self.publish_at <= timezone.now()
        )
        return publication_visible and self.has_member_access(user)

    def __str__(self):
        return self.title


class Comment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)
    is_hidden = models.BooleanField(default=False)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )

    def __str__(self):
        return "{0}: {1} - {2}".format(self.author, self.pub_date, self.video)


class Channel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to="channels/thumbnails", blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    subscribers = models.ManyToManyField(
        User, related_name="subscriptions", blank=True
    )

    def __str__(self):
        return self.name


class ChannelMembership(models.Model):
    class Role(models.TextChoices):
        EDITOR = "editor", "Editor"

    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="channel_memberships"
    )
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.EDITOR
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["channel", "user"], name="unique_channel_team_member"
            )
        ]

    def __str__(self):
        return f"{self.channel}: {self.user} ({self.get_role_display()})"


class ChannelTeamInvitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        REVOKED = "revoked", "Revoked"
        EXPIRED = "expired", "Expired"

    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name="team_invitations"
    )
    invitee = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="channel_team_invitations"
    )
    invited_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="sent_channel_team_invitations",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PENDING
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["channel", "invitee"],
                condition=Q(status="pending"),
                name="unique_pending_channel_team_invitation",
            )
        ]

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()

    def __str__(self):
        return f"{self.channel}: invite {self.invitee} ({self.get_status_display()})"


class Playlist(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        UNLISTED = "unlisted", "Unlisted"
        PRIVATE = "private", "Private"

    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="playlists"
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"], name="unique_playlist_name_per_owner"
            )
        ]

    def __str__(self):
        return self.name

    def can_view(self, user):
        return self.visibility != self.Visibility.PRIVATE or (
            user.is_authenticated and user.pk == self.owner_id
        )


class PlaylistItem(models.Model):
    playlist = models.ForeignKey(
        Playlist, on_delete=models.CASCADE, related_name="items"
    )
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, related_name="playlist_items"
    )
    position = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "added_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["playlist", "video"],
                name="unique_video_per_playlist",
            )
        ]

    def __str__(self):
        return f"{self.playlist}: {self.video}"


class WatchHistory(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="watch_history"
    )
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, related_name="history_entries"
    )
    watched_at = models.DateTimeField(auto_now=True)
    playback_position_seconds = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-watched_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "video"], name="unique_video_per_user_history"
            )
        ]

    def __str__(self):
        return f"{self.user}: {self.video}"


class Notification(models.Model):
    class Kind(models.TextChoices):
        COMMENT = "comment", "Comment"
        REPLY = "reply", "Reply"
        LIKE = "like", "Like"
        DISLIKE = "dislike", "Dislike"
        SUBSCRIPTION = "subscription", "Subscription"
        UPLOAD = "upload", "New upload"

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="sent_notifications"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, null=True, blank=True
    )
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    @property
    def is_read(self):
        return self.read_at is not None
