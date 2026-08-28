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

    def test_feed_renders_share_control_with_canonical_video_url(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-short-share")
        self.assertContains(response, f'data-share-url="{reverse("video_detail", args=[self.video.pk])}"')
        self.assertContains(response, 'data-share-title="Share This Short"')
        self.assertContains(response, 'aria-label="Share Share This Short"')

    def test_feed_uses_web_share_when_available(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "if(navigator.share)")
        self.assertContains(response, "await navigator.share({title,url})")
        self.assertContains(response, "new URL(button.dataset.shareUrl,window.location.origin).href")

    def test_feed_has_clipboard_and_legacy_copy_fallbacks(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "navigator.clipboard&&navigator.clipboard.writeText")
        self.assertContains(response, "await navigator.clipboard.writeText(url)")
        self.assertContains(response, "document.execCommand('copy')")
        self.assertContains(response, "button.textContent=copied?'Copied':'Copy failed'")

    def test_share_errors_do_not_break_feed(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "error.name==='AbortError'")
        self.assertContains(response, "button.textContent='Share failed'")
        self.assertContains(response, "shareButtons.forEach")
