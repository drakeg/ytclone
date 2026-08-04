from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to="categories/thumbnails")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to="videos/thumbnails")
    video_file = models.FileField(upload_to="videos/files")
    views = models.PositiveIntegerField(default=0)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    likes = models.ManyToManyField(User, related_name="likes", blank=True)
    dislikes = models.ManyToManyField(User, related_name="dislikes", blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0}: {1} - {2}".format(self.author, self.pub_date, self.video)


class Channel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to="channels/thumbnails")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    subscribers = models.ManyToManyField(
        User, related_name="subscriptions", blank=True
    )

    def __str__(self):
        return self.name


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
