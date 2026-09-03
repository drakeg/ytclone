from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Video
from .shorts_models import VideoShort


class ShortsPlaybackControlsTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="playback-creator", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Playback Channel", description="")
        self.video = Video.objects.create(
            title="Playback Short",
            description="Playback controls test",
            thumbnail="videos/thumbnails/playback.jpg",
            video_file="videos/files/playback.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.video)

    def test_feed_renders_accessible_playback_and_sound_controls(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-short-play")
        self.assertContains(response, "data-short-mute")
        self.assertContains(response, 'aria-label="Pause Playback Short"')
        self.assertContains(response, 'aria-label="Unmute Playback Short"')
        self.assertContains(response, 'aria-pressed="false"')

    def test_feed_supports_delegated_video_click_and_space_playback_toggle(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        self.assertIn("feed.addEventListener('click'", script)
        self.assertIn("e.target.matches?.('.shorts-video')", script)
        self.assertIn("e.code==='Space'", script)
        self.assertIn("togglePlay(activeIndex)", script)
        self.assertNotIn("v.addEventListener('click'", script)

    def test_feed_delegates_playback_state_events(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        self.assertIn("feed.addEventListener('play',syncPlaybackEvent,true)", script)
        self.assertIn("feed.addEventListener('pause',syncPlaybackEvent,true)", script)
        self.assertIn("if(Number.isInteger(i))syncPlay(i)", script)
        self.assertNotIn("v.addEventListener('play'", script)
        self.assertNotIn("v.addEventListener('pause'", script)

    def test_sound_preference_is_shared_across_feed_videos(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        self.assertIn("soundEnabled=false", script)
        self.assertIn("v.muted=!soundEnabled", script)
        self.assertIn("soundEnabled=!soundEnabled", script)
        self.assertIn("syncSound()", script)

    def test_existing_feed_navigation_and_lifecycle_controls_remain(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        self.assertIn("IntersectionObserver", script)
        self.assertIn("ArrowDown", script)
        self.assertIn("PageDown", script)
        self.assertIn("visibilitychange", script)
        self.assertIn("prefers-reduced-motion", script)
