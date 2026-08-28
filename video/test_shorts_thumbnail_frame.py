import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Channel, Video
from .services.short_clips import ShortClipError, create_short_from_video, rerender_short_from_source
from .shorts_forms import ShortClipForm
from .shorts_models import VideoShort


class ShortsThumbnailFrameTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.media_dir.cleanup)

        self.creator = User.objects.create_user(username="thumb-creator", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Thumbnail Channel", description="")
        self.source = Video.objects.create(
            title="Thumbnail Source",
            description="Source description",
            thumbnail=SimpleUploadedFile("source.jpg", b"source-thumb", content_type="image/jpeg"),
            video_file=SimpleUploadedFile("source.mp4", b"source-video", content_type="video/mp4"),
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )

    @staticmethod
    def fake_video_render(source_path, output_path, **kwargs):
        Path(output_path).write_bytes(b"rendered-short")

    @staticmethod
    def fake_thumbnail_render(source_path, output_path, **kwargs):
        Path(output_path).write_bytes(b"selected-frame")

    def test_form_rejects_thumbnail_frame_outside_clip(self):
        form = ShortClipForm({
            "title": "Bad thumbnail",
            "description": "",
            "start_seconds": 10,
            "end_seconds": 30,
            "thumbnail_frame_seconds": 31,
            "reframing_mode": VideoShort.ReframingMode.VERTICAL_CENTER,
            "overlay_text": "",
            "overlay_position": VideoShort.OverlayPosition.BOTTOM,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("thumbnail_frame_seconds", form.errors)

    @patch("video.services.short_clips._run_thumbnail_ffmpeg", side_effect=fake_thumbnail_render.__func__)
    @patch("video.services.short_clips._run_ffmpeg", side_effect=fake_video_render.__func__)
    def test_create_short_uses_selected_source_frame(self, unused_video_render, thumbnail_render):
        short = create_short_from_video(
            source_video=self.source,
            creator=self.creator,
            title="Frame Short",
            description="Description",
            start_seconds=5,
            end_seconds=25,
            thumbnail_frame_seconds=12,
        )
        self.assertEqual(Path(short.thumbnail.path).read_bytes(), b"selected-frame")
        self.assertEqual(short.short_metadata.thumbnail_frame_seconds, 12)
        self.assertEqual(thumbnail_render.call_args.kwargs["frame_seconds"], 12)

    @patch("video.services.short_clips._run_ffmpeg", side_effect=fake_video_render.__func__)
    def test_no_selected_frame_keeps_source_thumbnail_fallback(self, unused_video_render):
        short = create_short_from_video(
            source_video=self.source,
            creator=self.creator,
            title="Fallback Short",
            description="Description",
            start_seconds=0,
            end_seconds=20,
        )
        self.assertEqual(Path(short.thumbnail.path).read_bytes(), b"source-thumb")
        self.assertIsNone(short.short_metadata.thumbnail_frame_seconds)

    @patch("video.services.short_clips._run_thumbnail_ffmpeg", side_effect=fake_thumbnail_render.__func__)
    @patch("video.services.short_clips._run_ffmpeg", side_effect=fake_video_render.__func__)
    def test_rerender_replaces_thumbnail_and_persists_frame(self, unused_video_render, unused_thumbnail_render):
        short = create_short_from_video(
            source_video=self.source,
            creator=self.creator,
            title="Existing Short",
            description="Description",
            start_seconds=0,
            end_seconds=20,
        )
        old_thumbnail = short.thumbnail.name
        rerender_short_from_source(
            short=short,
            start_seconds=2,
            end_seconds=18,
            reframing_mode=VideoShort.ReframingMode.VERTICAL_CENTER,
            thumbnail_frame_seconds=10,
        )
        short.refresh_from_db()
        self.assertNotEqual(short.thumbnail.name, old_thumbnail)
        self.assertFalse(short.thumbnail.storage.exists(old_thumbnail))
        self.assertEqual(Path(short.thumbnail.path).read_bytes(), b"selected-frame")
        self.assertEqual(short.short_metadata.thumbnail_frame_seconds, 10)

    @patch("video.services.short_clips._run_thumbnail_ffmpeg", side_effect=ShortClipError("thumbnail failed"))
    @patch("video.services.short_clips._run_ffmpeg", side_effect=fake_video_render.__func__)
    def test_failed_thumbnail_generation_leaves_existing_short_untouched(self, unused_video_render, unused_thumbnail_render):
        short = create_short_from_video(
            source_video=self.source,
            creator=self.creator,
            title="Existing Short",
            description="Description",
            start_seconds=0,
            end_seconds=20,
        )
        old_video = short.video_file.name
        old_thumbnail = short.thumbnail.name
        with self.assertRaisesMessage(ShortClipError, "thumbnail failed"):
            rerender_short_from_source(
                short=short,
                start_seconds=1,
                end_seconds=19,
                reframing_mode=VideoShort.ReframingMode.VERTICAL_CENTER,
                thumbnail_frame_seconds=8,
            )
        short.refresh_from_db()
        self.assertEqual(short.video_file.name, old_video)
        self.assertEqual(short.thumbnail.name, old_thumbnail)
        self.assertIsNone(short.short_metadata.thumbnail_frame_seconds)

    def test_rerender_page_prepopulates_saved_thumbnail_frame(self):
        short = Video.objects.create(
            title="Saved Thumbnail Short",
            description="Description",
            thumbnail=SimpleUploadedFile("short.jpg", b"short-thumb", content_type="image/jpeg"),
            video_file=SimpleUploadedFile("short.mp4", b"short-video", content_type="video/mp4"),
            author=self.creator,
            channel=self.channel,
        )
        VideoShort.objects.create(
            video=short,
            source_video=self.source,
            source_start_seconds=5,
            source_end_seconds=25,
            thumbnail_frame_seconds=14,
        )
        self.client.force_login(self.creator)
        response = self.client.get(reverse("rerender_short", args=[short.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial["thumbnail_frame_seconds"], 14)
        self.assertContains(response, "Use current frame as thumbnail")
