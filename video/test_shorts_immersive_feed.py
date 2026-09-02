from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Video
from .shorts_models import VideoShort


class ShortsImmersiveFeedTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="feed-creator", password="password123")
        self.viewer = User.objects.create_user(username="feed-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Feed Channel", description="")
        self.shorts = []
        for index in range(2):
            video = Video.objects.create(
                title=f"Feed Short {index + 1}",
                description=f"Description {index + 1}",
                thumbnail=f"videos/thumbnails/feed-{index}.jpg",
                video_file=f"videos/files/feed-{index}.mp4",
                author=self.creator,
                channel=self.channel,
                publication_status=Video.PublicationStatus.PUBLISHED,
            )
            VideoShort.objects.create(video=video)
            self.shorts.append(video)

    def test_feed_renders_snap_aligned_one_short_items(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="shorts-feed"')
        self.assertContains(response, 'data-short-count="2"')
        self.assertContains(response, 'data-short-index="0"')
        self.assertContains(response, 'data-short-index="1"')
        css = Path("video/static/video/shorts.css").read_text(encoding="utf-8")
        self.assertIn("scroll-snap-type:y mandatory", css)
        self.assertIn("scroll-snap-align:start", css)

    def test_feed_video_surfaces_default_muted_for_autoplay(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, 'class="shorts-video"', count=2)
        self.assertContains(response, "playsinline muted loop", count=2)
        self.assertContains(response, 'class="btn btn-sm btn-dark shorts-mute"', count=2)
        self.assertContains(response, ">Unmute</button>", count=2)

    def test_feed_includes_keyboard_and_visibility_lifecycle_logic(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        self.assertIn("IntersectionObserver", script)
        self.assertIn("ArrowDown", script)
        self.assertIn("PageDown", script)
        self.assertIn("visibilitychange", script)
        self.assertIn("prefers-reduced-motion", script)

    def test_existing_viewer_actions_remain_available(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("shorts_feed"))
        for video in self.shorts:
            self.assertContains(response, reverse("like_short", args=[video.pk]))
            self.assertContains(response, reverse("dislike_short", args=[video.pk]))
            self.assertContains(response, reverse("video_detail", args=[video.pk]) + "#comments-heading")
            self.assertContains(response, reverse("report_content", args=["video", video.pk]))

    def test_feed_still_honors_visibility_rules(self):
        hidden = Video.objects.create(
            title="Hidden Feed Short",
            description="",
            thumbnail="videos/thumbnails/hidden-feed.jpg",
            video_file="videos/files/hidden-feed.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        VideoShort.objects.create(video=hidden)
        response = self.client.get(reverse("shorts_feed"))
        self.assertNotContains(response, hidden.title)
        self.assertContains(response, self.shorts[0].title)
        self.assertContains(response, self.shorts[1].title)
