from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Video
from .shorts_models import VideoShort


class ShortsShareControllerTests(TestCase):
    def setUp(self):
        creator = User.objects.create_user(username="share-controller-creator", password="password123")
        channel = Channel.objects.create(owner=creator, name="Share Controller", description="")
        video = Video.objects.create(
            title="Share Controller Short",
            description="",
            thumbnail="videos/thumbnails/share-controller.jpg",
            video_file="videos/files/share-controller.mp4",
            author=creator,
            channel=channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=video)

    def test_shorts_feed_loads_namespaced_share_controller_only_on_shorts(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "video/shorts_share.js")

        response = self.client.get(reverse("video_list"))
        self.assertNotContains(response, "video/shorts_share.js")

    def test_share_controller_preserves_native_share_and_copy_fallbacks(self):
        script = Path("video/static/video/shorts_share.js").read_text(encoding="utf-8")

        self.assertIn("navigator.share", script)
        self.assertIn("navigator.clipboard?.writeText", script)
        self.assertIn('document.execCommand("copy")', script)
        self.assertIn('button.textContent = copied ? "Copied" : "Copy failed";', script)
        self.assertIn('button.textContent = "Share failed";', script)
        self.assertIn('error?.name === "AbortError"', script)

    def test_share_controller_owns_share_click_before_inline_fallback(self):
        script = Path("video/static/video/shorts_share.js").read_text(encoding="utf-8")

        self.assertIn('feed.addEventListener(', script)
        self.assertIn('"click"', script)
        self.assertIn('event.stopImmediatePropagation();', script)
        self.assertIn('"[data-short-share]"', script)
        self.assertIn("true,", script)
