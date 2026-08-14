from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import VideoEditForm
from .models import Category, Channel, Playlist, PlaylistItem, Video, WatchHistory


class PublishingTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.category = Category.objects.create(name="General", description="General", thumbnail="categories/general.jpg")
        self.channel = Channel.objects.create(name="Channel", description="Channel", thumbnail="channels/channel.jpg", owner=self.creator)

    def video(self, title, status, publish_at=None):
        return Video.objects.create(title=title, description=title, thumbnail=f"videos/{title}.jpg", video_file=f"videos/{title}.mp4", author=self.creator, channel=self.channel, category=self.category, publication_status=status, publish_at=publish_at)

    def test_existing_default_is_published(self):
        video = Video.objects.create(title="Default", description="Default", thumbnail="videos/default.jpg", video_file="videos/default.mp4", author=self.creator, channel=self.channel, category=self.category)
        self.assertEqual(video.publication_status, Video.PublicationStatus.PUBLISHED)

    def test_draft_and_future_schedule_are_owner_only(self):
        draft = self.video("Draft", Video.PublicationStatus.DRAFT)
        scheduled = self.video("Future", Video.PublicationStatus.SCHEDULED, timezone.now() + timedelta(days=1))
        for video in [draft, scheduled]:
            url = reverse("video_detail", kwargs={"pk": video.pk})
            self.assertEqual(self.client.get(url).status_code, 404)
            self.client.login(username="creator", password="password123")
            self.assertEqual(self.client.get(url).status_code, 200)
            self.client.logout()

    def test_due_scheduled_video_is_public(self):
        video = self.video("Due", Video.PublicationStatus.SCHEDULED, timezone.now() - timedelta(minutes=1))
        self.assertEqual(self.client.get(reverse("video_detail", kwargs={"pk": video.pk})).status_code, 200)

    def test_scheduled_form_requires_future_time(self):
        data = {"title": "Scheduled", "description": "Scheduled", "category": self.category.pk, "channel": self.channel.pk, "publication_status": "scheduled", "publish_at": timezone.now() - timedelta(minutes=1)}
        form = VideoEditForm(data=data, instance=self.video("Edit", Video.PublicationStatus.PUBLISHED), user=self.creator)
        self.assertFalse(form.is_valid())
        self.assertIn("publish_at", form.errors)

    def test_non_scheduled_status_clears_publish_time(self):
        video = self.video("Edit", Video.PublicationStatus.SCHEDULED, timezone.now() + timedelta(days=1))
        form = VideoEditForm(data={"title": "Edit", "description": "Edit", "category": self.category.pk, "channel": self.channel.pk, "publication_status": "draft"}, instance=video, user=self.creator)
        self.assertTrue(form.is_valid(), form.errors)
        updated = form.save()
        self.assertIsNone(updated.publish_at)

    def test_public_surfaces_hide_unpublished_videos(self):
        draft = self.video("Private Draft", Video.PublicationStatus.DRAFT)
        playlist = Playlist.objects.create(owner=self.viewer, name="Public list", visibility=Playlist.Visibility.PUBLIC)
        PlaylistItem.objects.create(playlist=playlist, video=draft)
        WatchHistory.objects.create(user=self.viewer, video=draft)
        urls = [
            reverse("video_list"),
            reverse("search") + "?query=Private",
            reverse("channel_detail", kwargs={"pk": self.channel.pk}),
            reverse("category_detail", kwargs={"pk": self.category.pk}),
            reverse("user_profile", kwargs={"username": self.creator.username}),
            reverse("playlist_detail", kwargs={"pk": playlist.pk}),
        ]
        for url in urls:
            self.assertNotContains(self.client.get(url), draft.title)
        self.client.login(username="viewer", password="password123")
        self.assertNotContains(self.client.get(reverse("watch_history")), draft.title)

    def test_owner_discovery_includes_own_draft(self):
        draft = self.video("Owner Draft", Video.PublicationStatus.DRAFT)
        self.client.login(username="creator", password="password123")
        response = self.client.get(reverse("video_list"))
        self.assertIn(draft, response.context["sections"].newest_videos)
