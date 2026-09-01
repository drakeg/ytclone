from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Video
from .shorts_models import VideoShort


class ShortsFeedControllerTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.short = Video.objects.create(
            title="Controller Short",
            description="Short",
            thumbnail="videos/short.jpg",
            video_file="videos/short.mp4",
            author=self.creator,
        )
        VideoShort.objects.create(video=self.short)

    def test_namespaced_controller_loads_only_on_shorts_feed(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "video/shorts_feed.js")
        self.assertContains(response, "video/shorts_reply_ajax.js")
        self.assertContains(response, "video/shorts_reaction_ajax.js")
        self.assertContains(response, "video/shorts_playback_accessibility.js")
        self.assertContains(response, "video/shorts_share.js")

        response = self.client.get(reverse("video_list"))
        self.assertNotContains(response, "video/shorts_feed.js")

    def test_template_contains_no_inline_executable_javascript(self):
        template = Path("video/templates/videos/shorts_feed.html").read_text(encoding="utf-8")
        self.assertNotIn("<script", template)
        self.assertNotIn("IntersectionObserver", template)

    def test_controller_preserves_feed_initialization_and_playback_hooks(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        for token in (
            "document.getElementById('shorts-feed')",
            "if(!feed)return",
            "IntersectionObserver",
            "scrollIntoView",
            "visibilitychange",
            "prefers-reduced-motion",
            "data-short-play",
            "data-short-mute",
        ):
            with self.subTest(token=token):
                self.assertIn(token, script)

    def test_controller_preserves_social_progressive_enhancement_hooks(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        for token in (
            "data-short-reaction-form",
            "data-short-subscribe-form",
            "data-short-comment-form",
            "data-short-share",
            "X-Requested-With",
            "XMLHttpRequest",
            "new FormData(form)",
        ):
            with self.subTest(token=token):
                self.assertIn(token, script)
