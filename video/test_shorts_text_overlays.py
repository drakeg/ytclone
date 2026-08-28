import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Channel, Video
from .services.short_clips import create_short_from_video, rerender_short_from_source
from .shorts_forms import ShortClipForm
from .shorts_models import VideoShort


class ShortsTextOverlayTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.media_dir.cleanup)

        self.creator = User.objects.create_user(username="overlay-creator", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Overlay Channel", description="")
        self.source = Video.objects.create(
            title="Overlay Source",
            description="Source description",
            thumbnail=SimpleUploadedFile("source.jpg", b"thumbnail", content_type="image/jpeg"),
            video_file=SimpleUploadedFile("source.mp4", b"source-video", content_type="video/mp4"),
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )

    @staticmethod
    def fake_ffmpeg(source_path, output_path, **kwargs):
        Path(output_path).write_bytes(b"rendered-short")

    def test_form_exposes_optional_overlay_controls(self):
        form = ShortClipForm()
        self.assertFalse(form.fields["overlay_text"].required)
        self.assertEqual(form.fields["overlay_text"].max_length, 120)
        self.assertEqual(
            list(form.fields["overlay_position"].choices),
            [("top", "Top"), ("center", "Center"), ("bottom", "Bottom")],
        )

    @patch("video.services.short_clips._run_ffmpeg", side_effect=fake_ffmpeg.__func__)
    def test_create_short_persists_overlay_settings(self, mocked_ffmpeg):
        short = create_short_from_video(
            source_video=self.source,
            creator=self.creator,
            title="Overlay Short",
            description="Description",
            start_seconds=5,
            end_seconds=25,
            reframing_mode=VideoShort.ReframingMode.VERTICAL_CENTER,
            overlay_text="Watch this part",
            overlay_position=VideoShort.OverlayPosition.TOP,
        )
        metadata = short.short_metadata
        self.assertEqual(metadata.overlay_text, "Watch this part")
        self.assertEqual(metadata.overlay_position, VideoShort.OverlayPosition.TOP)
        call_kwargs = mocked_ffmpeg.call_args.kwargs
        self.assertEqual(call_kwargs["overlay_text"], "Watch this part")
        self.assertEqual(call_kwargs["overlay_position"], VideoShort.OverlayPosition.TOP)

    @patch("video.services.short_clips._run_ffmpeg", side_effect=fake_ffmpeg.__func__)
    def test_rerender_updates_overlay_without_changing_video_identity(self, unused_ffmpeg):
        short = create_short_from_video(
            source_video=self.source,
            creator=self.creator,
            title="Existing Overlay Short",
            description="Description",
            start_seconds=0,
            end_seconds=20,
            overlay_text="Old text",
            overlay_position=VideoShort.OverlayPosition.BOTTOM,
        )
        original_pk = short.pk
        rerender_short_from_source(
            short=short,
            start_seconds=2,
            end_seconds=18,
            reframing_mode=VideoShort.ReframingMode.VERTICAL_RIGHT,
            overlay_text="New text",
            overlay_position=VideoShort.OverlayPosition.CENTER,
        )
        short.refresh_from_db()
        metadata = short.short_metadata
        self.assertEqual(short.pk, original_pk)
        self.assertEqual(metadata.overlay_text, "New text")
        self.assertEqual(metadata.overlay_position, VideoShort.OverlayPosition.CENTER)
        self.assertEqual(metadata.source_start_seconds, 2)
        self.assertEqual(metadata.source_end_seconds, 18)

    def test_overlay_text_length_is_enforced(self):
        form = ShortClipForm(
            {
                "title": "Too much text",
                "description": "",
                "start_seconds": 0,
                "end_seconds": 20,
                "reframing_mode": VideoShort.ReframingMode.VERTICAL_CENTER,
                "overlay_text": "x" * 121,
                "overlay_position": VideoShort.OverlayPosition.BOTTOM,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("overlay_text", form.errors)

    def test_rerender_page_prepopulates_saved_overlay(self):
        short = Video.objects.create(
            title="Saved Overlay Short",
            description="Description",
            thumbnail=SimpleUploadedFile("short.jpg", b"thumbnail", content_type="image/jpeg"),
            video_file=SimpleUploadedFile("short.mp4", b"short-video", content_type="video/mp4"),
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        VideoShort.objects.create(
            video=short,
            source_video=self.source,
            source_start_seconds=4,
            source_end_seconds=24,
            reframing_mode=VideoShort.ReframingMode.VERTICAL_LEFT,
            overlay_text="Saved text",
            overlay_position=VideoShort.OverlayPosition.TOP,
        )
        self.client.force_login(self.creator)
        response = self.client.get(reverse("rerender_short", args=[short.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Saved text")
        self.assertEqual(response.context["form"].fields["overlay_position"].initial, VideoShort.OverlayPosition.TOP)
