import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Video, WatchHistory
from .services.discovery import get_discovery_sections


class ContinueWatchingTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="creator", password="password123"
        )
        self.viewer = User.objects.create_user(
            username="viewer", password="password123"
        )
        self.other_viewer = User.objects.create_user(
            username="other-viewer", password="password123"
        )
        self.category = Category.objects.create(
            name="General",
            description="General videos",
            thumbnail="categories/thumbnails/general.jpg",
        )
        self.video = self.create_video("Progress video")

    def create_video(self, title):
        return Video.objects.create(
            title=title,
            description=f"Description for {title}",
            thumbnail=f"videos/thumbnails/{title}.jpg",
            video_file=f"videos/files/{title}.mp4",
            author=self.creator,
            category=self.category,
        )

    def progress_url(self, video=None):
        return reverse(
            "playback_progress", kwargs={"pk": (video or self.video).pk}
        )

    def post_progress(self, position, duration, video=None):
        return self.client.post(
            self.progress_url(video),
            data=json.dumps(
                {
                    "position_seconds": position,
                    "duration_seconds": duration,
                }
            ),
            content_type="application/json",
        )

    def test_progress_endpoint_requires_login(self):
        response = self.post_progress(30, 120)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
        self.assertFalse(WatchHistory.objects.exists())

    def test_progress_endpoint_rejects_get(self):
        self.client.login(username="viewer", password="password123")

        response = self.client.get(self.progress_url())

        self.assertEqual(response.status_code, 405)

    def test_authenticated_progress_is_saved_and_returned(self):
        self.client.login(username="viewer", password="password123")

        response = self.post_progress(31.6, 120.2)

        self.assertEqual(response.status_code, 200)
        entry = WatchHistory.objects.get(user=self.viewer, video=self.video)
        self.assertEqual(entry.playback_position_seconds, 32)
        self.assertEqual(entry.duration_seconds, 120)
        self.assertEqual(
            response.json(),
            {"position_seconds": 32, "duration_seconds": 120},
        )

    def test_progress_is_clamped_to_valid_bounds(self):
        self.client.login(username="viewer", password="password123")

        negative_response = self.post_progress(-20, 120)
        beyond_response = self.post_progress(500, 120)

        self.assertEqual(negative_response.json()["position_seconds"], 0)
        self.assertEqual(beyond_response.json()["position_seconds"], 120)
        entry = WatchHistory.objects.get(user=self.viewer, video=self.video)
        self.assertEqual(entry.playback_position_seconds, 120)

    def test_invalid_progress_payloads_are_rejected(self):
        self.client.login(username="viewer", password="password123")
        responses = [
            self.client.post(
                self.progress_url(), data="not-json", content_type="application/json"
            ),
            self.post_progress("not-a-number", 120),
            self.post_progress(10, 0),
            self.post_progress(float("inf"), 120),
        ]

        self.assertTrue(all(response.status_code == 400 for response in responses))
        self.assertFalse(WatchHistory.objects.exists())

    def test_saving_progress_does_not_change_another_users_entry(self):
        other_entry = WatchHistory.objects.create(
            user=self.other_viewer,
            video=self.video,
            playback_position_seconds=70,
            duration_seconds=120,
        )
        self.client.login(username="viewer", password="password123")

        self.post_progress(20, 120)

        other_entry.refresh_from_db()
        self.assertEqual(other_entry.playback_position_seconds, 70)
        self.assertEqual(
            WatchHistory.objects.get(user=self.viewer).playback_position_seconds,
            20,
        )

    def test_video_detail_exposes_only_current_users_resume_position(self):
        WatchHistory.objects.create(
            user=self.viewer,
            video=self.video,
            playback_position_seconds=45,
            duration_seconds=120,
        )
        WatchHistory.objects.create(
            user=self.other_viewer,
            video=self.video,
            playback_position_seconds=90,
            duration_seconds=120,
        )
        self.client.login(username="viewer", password="password123")

        response = self.client.get(
            reverse("video_detail", kwargs={"pk": self.video.pk})
        )

        self.assertEqual(response.context["history_entry"].playback_position_seconds, 45)
        self.assertContains(response, 'data-resume-position="45"')
        self.assertNotContains(response, 'data-resume-position="90"')

    def test_continue_watching_is_ordered_and_excludes_completed_videos(self):
        older = self.video
        newer = self.create_video("Newer progress")
        completed = self.create_video("Completed")
        older_entry = WatchHistory.objects.create(
            user=self.viewer,
            video=older,
            playback_position_seconds=20,
            duration_seconds=120,
        )
        WatchHistory.objects.create(
            user=self.viewer,
            video=newer,
            playback_position_seconds=60,
            duration_seconds=120,
        )
        WatchHistory.objects.create(
            user=self.viewer,
            video=completed,
            playback_position_seconds=118,
            duration_seconds=120,
        )
        WatchHistory.objects.filter(pk=older_entry.pk).update(
            watched_at=timezone.now() - timedelta(days=1)
        )

        videos = list(get_discovery_sections(self.viewer).continue_watching_videos)

        self.assertEqual(videos, [newer, older])
        self.assertNotIn(completed, videos)
        self.assertEqual(videos[0].resume_position_seconds, 60)

    def test_homepage_shows_continue_watching_only_when_authenticated(self):
        WatchHistory.objects.create(
            user=self.viewer,
            video=self.video,
            playback_position_seconds=30,
            duration_seconds=120,
        )

        anonymous_response = self.client.get(reverse("video_list"))
        self.client.login(username="viewer", password="password123")
        authenticated_response = self.client.get(reverse("video_list"))

        self.assertNotContains(anonymous_response, "Continue watching")
        self.assertContains(authenticated_response, "Continue watching")
        self.assertContains(authenticated_response, self.video.title)
