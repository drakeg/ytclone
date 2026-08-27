import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Channel, Video
from .services.short_clips import ShortClipError, _vertical_filter, create_short_from_video
from .shorts_forms import ShortClipForm
from .shorts_models import VideoShort


class ShortsVerticalReframingTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.media_dir.cleanup)

        self.creator = User.objects.create_user(username="creator", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Crop Channel", description="")
        self.source = Video.objects.create(
            title="Landscape Source",
            description="Source",
            thumbnail=SimpleUploadedFile("source.jpg", b"thumbnail", content_type="image/jpeg"),
            video_file=SimpleUploadedFile("source.mp4", b"video", content_type="video/mp4"),
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )

    @staticmethod
    def fake_ffmpeg(source_path, output_path, **kwargs):
        Path(output_path).write_bytes(b"vertical-short")

    def test_form_offers_original_and_three_vertical_focus_modes(self):
        form = ShortClipForm()
        values = [value for value, unused_label in form.fields["reframing_mode"].choices]
        self.assertEqual(
            values,
            ["original", "vertical_left", "vertical_center", "vertical_right"],
        )
        self.assertEqual(form.fields["reframing_mode"].initial, "vertical_center")

    def test_legacy_post_without_framing_preserves_original_mode(self):
        form = ShortClipForm(
            {
                "title": "Legacy",
                "description": "",
                "start_seconds": 0,
                "end_seconds": 30,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["reframing_mode"], VideoShort.ReframingMode.ORIGINAL)

    def test_vertical_filters_use_deterministic_horizontal_focus(self):
        left = _vertical_filter(VideoShort.ReframingMode.VERTICAL_LEFT)
        center = _vertical_filter(VideoShort.ReframingMode.VERTICAL_CENTER)
        right = _vertical_filter(VideoShort.ReframingMode.VERTICAL_RIGHT)
        self.assertIn("crop=720:1280:0:(ih-1280)/2", left)
        self.assertIn("crop=720:1280:(iw-720)/2:(ih-1280)/2", center)
        self.assertIn("crop=720:1280:iw-720:(ih-1280)/2", right)
        for filter_value in (left, center, right):
            self.assertIn("scale=720:1280:force_original_aspect_ratio=increase", filter_value)

    @patch("video.services.short_clips._run_ffmpeg", side_effect=fake_ffmpeg.__func__)
    def test_service_persists_selected_reframing_mode(self, ffmpeg):
        short = create_short_from_video(
            source_video=self.source,
            creator=self.creator,
            title="Vertical Derived Short",
            description="",
            start_seconds=5,
            end_seconds=35,
            reframing_mode=VideoShort.ReframingMode.VERTICAL_RIGHT,
        )
        metadata = VideoShort.objects.get(video=short)
        self.assertEqual(metadata.reframing_mode, VideoShort.ReframingMode.VERTICAL_RIGHT)
        self.assertEqual(ffmpeg.call_args.kwargs["reframing_mode"], VideoShort.ReframingMode.VERTICAL_RIGHT)

    def test_service_rejects_unknown_reframing_mode(self):
        with self.assertRaisesMessage(ShortClipError, "valid Short framing option"):
            create_short_from_video(
                source_video=self.source,
                creator=self.creator,
                title="Bad framing",
                description="",
                start_seconds=0,
                end_seconds=30,
                reframing_mode="follow_the_face",
            )

    def test_clip_page_contains_visual_framing_preview(self):
        self.client.force_login(self.creator)
        response = self.client.get(reverse("create_short_from_long_form", args=[self.source.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose the output frame")
        self.assertContains(response, "Approximate 9:16 crop preview")
        self.assertContains(response, 'id="id_reframing_mode"')
        self.assertContains(response, "vertical_center")
