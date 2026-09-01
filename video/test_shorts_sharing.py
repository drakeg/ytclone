from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Video
from .shorts_models import VideoShort


class ShortsSharingTests(TestCase):
    def setUp(self):
        creator = User.objects.create_user(username="share-creator", password="password123")
        channel = Channel.objects.create(owner=creator, name="Share Channel", description="")
        self.video = Video.objects.create(
            title="Share This Short",
            description="Sharing test",
            thumbnail="videos/thumbnails/share.jpg",
            video_file="videos/files/share.mp4",
            author=creator,
            channel=channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.video)

    def _share_script(self):
        return Path("video/static/video/shorts_share.js").read_text(encoding="utf-8")

    def test_feed_renders_share_control_with_canonical_video_url(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-short-share")
        self.assertContains(response, f'data-share-url="{reverse("video_detail", args=[self.video.pk])}"')
        self.assertContains(response, 'data-share-title="Share This Short"')
        self.assertContains(response, 'aria-label="Share Share This Short"')

    def test_feed_uses_web_share_when_available(self):
        script = self._share_script()
        self.assertIn("if (navigator.share)", script)
        self.assertIn("await navigator.share({title, url})", script)
        self.assertIn("new URL(button.dataset.shareUrl, window.location.origin).href", script)

    def test_feed_has_clipboard_and_legacy_copy_fallbacks(self):
        script = self._share_script()
        self.assertIn("navigator.clipboard?.writeText", script)
        self.assertIn("await navigator.clipboard.writeText(url)", script)
        self.assertIn('document.execCommand("copy")', script)
        self.assertIn('button.textContent = copied ? "Copied" : "Copy failed"', script)

    def test_share_errors_do_not_break_feed(self):
        script = self._share_script()
        self.assertIn('error?.name === "AbortError"', script)
        self.assertIn('button.textContent = "Share failed"', script)
        self.assertIn('event.stopImmediatePropagation()', script)
