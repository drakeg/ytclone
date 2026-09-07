from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Channel, Video


class WatchAutoplayNextTests(TestCase):
    def setUp(self):
        creator = User.objects.create_user(username="autoplay-creator", password="password123")
        channel = Channel.objects.create(owner=creator, name="Autoplay Channel", description="")
        category = Category.objects.create(name="Autoplay")
        self.current = Video.objects.create(
            title="Current autoplay video",
            description="",
            thumbnail="videos/thumbnails/current-autoplay.jpg",
            video_file="videos/files/current-autoplay.mp4",
            author=creator,
            channel=channel,
            category=category,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        self.next_video = Video.objects.create(
            title="Next autoplay video",
            description="",
            thumbnail="videos/thumbnails/next-autoplay.jpg",
            video_file="videos/files/next-autoplay.mp4",
            author=creator,
            channel=channel,
            category=category,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )

    def test_watch_page_exposes_first_recommendation_and_toggle(self):
        response = self.client.get(reverse("video_detail", args=[self.current.pk]))

        self.assertContains(response, "data-watch-next")
        self.assertContains(response, f'data-watch-next-url="{reverse("video_detail", args=[self.next_video.pk])}"')
        self.assertContains(response, "data-autoplay-toggle")
        self.assertContains(response, 'aria-pressed="true"')
        self.assertContains(response, "video/watch_autoplay_next.js")

    def test_autoplay_script_is_scoped_to_video_detail(self):
        response = self.client.get(reverse("video_list"))
        self.assertNotContains(response, "video/watch_autoplay_next.js")

    def test_controller_persists_preference_and_waits_before_navigation(self):
        with open("video/static/video/watch_autoplay_next.js", encoding="utf-8") as script_file:
            script = script_file.read()

        self.assertIn('const STORAGE_KEY = "videoshare.autoplayNext";', script)
        self.assertIn("const COUNTDOWN_SECONDS = 5;", script)
        self.assertIn('player.addEventListener("ended", startCountdown);', script)
        self.assertIn('player.addEventListener("play", clearCountdown);', script)
        self.assertIn("window.localStorage.setItem", script)
        self.assertIn("window.location.assign(nextCard.dataset.watchNextUrl);", script)
        self.assertIn('status.textContent = `Next video in ${secondsRemaining}s`;', script)
