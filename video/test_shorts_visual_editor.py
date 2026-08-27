from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Video
from .shorts_forms import ShortClipForm


class ShortsVisualEditorTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="visual-short-creator", password="password123"
        )
        self.channel = Channel.objects.create(
            owner=self.creator,
            name="Visual Shorts Channel",
            description="Visual clip editor tests",
        )
        self.source = Video.objects.create(
            title="Long source for visual editor",
            description="Source video",
            thumbnail="videos/thumbnails/visual-source.jpg",
            video_file="videos/files/visual-source.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )

    def test_clip_page_renders_visual_selector_and_manual_fallback(self):
        self.client.force_login(self.creator)
        response = self.client.get(
            reverse("create_short_from_long_form", args=[self.source.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="visual-clip-editor"', html=False)
        self.assertContains(response, 'id="short-start-range"', html=False)
        self.assertContains(response, 'id="short-end-range"', html=False)
        self.assertContains(response, "Set start to current time")
        self.assertContains(response, "Set end to current time")
        self.assertContains(response, "Preview selected clip")
        self.assertContains(response, 'id="id_start_seconds"', html=False)
        self.assertContains(response, 'id="id_end_seconds"', html=False)

    def test_visual_editor_keeps_server_validation_contract(self):
        form = ShortClipForm(
            {
                "title": "Too long",
                "description": "",
                "start_seconds": 10,
                "end_seconds": 191,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("180 seconds or shorter", form.errors["end_seconds"][0])

    def test_visual_editor_markup_contains_client_side_clip_limit(self):
        self.client.force_login(self.creator)
        response = self.client.get(
            reverse("create_short_from_long_form", args=[self.source.pk])
        )
        body = response.content.decode()
        self.assertIn("const maxClipLength = 180;", body)
        self.assertIn("loadedmetadata", body)
        self.assertIn("timeupdate", body)
        self.assertIn("Selected duration:", body)

    def test_non_owner_cannot_access_visual_editor(self):
        other = User.objects.create_user(username="other-viewer", password="password123")
        self.client.force_login(other)
        response = self.client.get(
            reverse("create_short_from_long_form", args=[self.source.pk])
        )
        self.assertEqual(response.status_code, 403)
