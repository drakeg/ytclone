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

    def test_feed_supports_video_click_and_space_playback_toggle(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "v.addEventListener('click',()=>togglePlay(i))")
        self.assertContains(response, "e.code==='Space'")
        self.assertContains(response, "togglePlay(activeIndex)")
        self.assertContains(response, "v.addEventListener('play',()=>syncPlay(i))")
        self.assertContains(response, "v.addEventListener('pause',()=>syncPlay(i))")

    def test_sound_preference_is_shared_across_feed_videos(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "soundEnabled=false")
        self.assertContains(response, "v.muted=!soundEnabled")
        self.assertContains(response, "soundEnabled=!soundEnabled")
        self.assertContains(response, "syncSound()")

    def test_existing_feed_navigation_and_lifecycle_controls_remain(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "IntersectionObserver")
        self.assertContains(response, "ArrowDown")
        self.assertContains(response, "PageDown")
        self.assertContains(response, "visibilitychange")
        self.assertContains(response, "prefers-reduced-motion")
