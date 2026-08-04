from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Video, WatchHistory


class WatchHistoryTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.other_viewer = User.objects.create_user(
            username="other-viewer", password="password123"
        )
        self.category = Category.objects.create(
            name="General",
            description="General videos",
            thumbnail="categories/thumbnails/general.jpg",
        )
        self.video = Video.objects.create(
            title="History test video",
            description="A test video",
            thumbnail="videos/thumbnails/history.jpg",
            video_file="videos/files/history.mp4",
            author=self.owner,
            category=self.category,
        )

    def test_anonymous_view_does_not_create_history(self):
        self.client.get(reverse("video_detail", kwargs={"pk": self.video.pk}))
        self.assertEqual(WatchHistory.objects.count(), 0)

    def test_authenticated_view_creates_one_history_entry(self):
        self.client.login(username="viewer", password="password123")
        url = reverse("video_detail", kwargs={"pk": self.video.pk})

        self.client.get(url)
        self.client.get(url)

        self.assertEqual(WatchHistory.objects.count(), 1)
        entry = WatchHistory.objects.get()
        self.assertEqual(entry.user, self.viewer)
        self.assertEqual(entry.video, self.video)

    def test_history_page_requires_login(self):
        response = self.client.get(reverse("watch_history"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_history_page_only_shows_current_users_entries(self):
        WatchHistory.objects.create(user=self.viewer, video=self.video)
        WatchHistory.objects.create(user=self.other_viewer, video=self.video)
        self.client.login(username="viewer", password="password123")

        response = self.client.get(reverse("watch_history"))

        self.assertContains(response, self.video.title)
        self.assertEqual(list(response.context["entries"]), [self.viewer.watch_history.get()])

    def test_user_can_remove_own_history_entry(self):
        entry = WatchHistory.objects.create(user=self.viewer, video=self.video)
        self.client.login(username="viewer", password="password123")

        response = self.client.post(
            reverse("watch_history_remove", kwargs={"pk": entry.pk})
        )

        self.assertRedirects(response, reverse("watch_history"))
        self.assertFalse(WatchHistory.objects.filter(pk=entry.pk).exists())

    def test_user_cannot_remove_another_users_history_entry(self):
        entry = WatchHistory.objects.create(user=self.other_viewer, video=self.video)
        self.client.login(username="viewer", password="password123")

        response = self.client.post(
            reverse("watch_history_remove", kwargs={"pk": entry.pk})
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(WatchHistory.objects.filter(pk=entry.pk).exists())

    def test_clear_history_removes_only_current_users_entries(self):
        WatchHistory.objects.create(user=self.viewer, video=self.video)
        WatchHistory.objects.create(user=self.other_viewer, video=self.video)
        self.client.login(username="viewer", password="password123")

        response = self.client.post(reverse("watch_history_clear"))

        self.assertRedirects(response, reverse("watch_history"))
        self.assertFalse(WatchHistory.objects.filter(user=self.viewer).exists())
        self.assertTrue(WatchHistory.objects.filter(user=self.other_viewer).exists())
