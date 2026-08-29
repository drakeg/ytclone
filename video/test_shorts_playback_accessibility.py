from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Video
from .shorts_models import VideoShort


class ShortsPlaybackAccessibilityTests(TestCase):
    def setUp(self):
        creator = User.objects.create_user(username="playback-a11y-creator", password="password123")
        channel = Channel.objects.create(owner=creator, name="Playback Accessibility", description="")
        video = Video.objects.create(
            title="Accessible Short",
            description="",
            thumbnail="videos/thumbnails/accessible.jpg",
            video_file="videos/files/accessible.mp4",
            author=creator,
            channel=channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=video)

    def test_feed_loads_playback_accessibility_enhancement_only_on_shorts(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "video/shorts_playback_accessibility.js")

        response = self.client.get(reverse("video_list"))
        self.assertNotContains(response, "video/shorts_playback_accessibility.js")

    def test_script_uses_action_label_and_removes_pressed_state(self):
        with open("video/static/video/shorts_playback_accessibility.js", encoding="utf-8") as script_file:
            script = script_file.read()

        self.assertIn('const action = video.paused ? "Play" : "Pause";', script)
        self.assertIn('button.setAttribute("aria-label", `${action} ${title}`);', script)
        self.assertIn('button.removeAttribute("aria-pressed");', script)
        self.assertIn('video.addEventListener("play"', script)
        self.assertIn('video.addEventListener("pause"', script)

    def test_mute_control_keeps_pressed_state_contract(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "data-short-mute")
        self.assertContains(response, 'aria-label="Unmute Accessible Short"')
        self.assertContains(response, 'aria-pressed="false"')
