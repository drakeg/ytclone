import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Channel, Video
from .services.short_clips import ShortClipError, rerender_short_from_source
from .shorts_models import VideoShort


class ShortsRerenderTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.media_dir.cleanup)
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Rerender Channel", description="")
        self.source = Video.objects.create(
            title="Source", description="Source", author=self.creator, channel=self.channel,
            thumbnail=SimpleUploadedFile("source.jpg", b"thumb", content_type="image/jpeg"),
            video_file=SimpleUploadedFile("source.mp4", b"source-video", content_type="video/mp4"),
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        self.short = Video.objects.create(
            title="Existing Short", description="Keep me", author=self.creator, channel=self.channel,
            thumbnail=SimpleUploadedFile("short.jpg", b"short-thumb", content_type="image/jpeg"),
            video_file=SimpleUploadedFile("short.mp4", b"old-short", content_type="video/mp4"),
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(
            video=self.short, source_video=self.source, source_start_seconds=10,
            source_end_seconds=40, reframing_mode=VideoShort.ReframingMode.VERTICAL_CENTER,
        )

    @staticmethod
    def fake_ffmpeg(source_path, output_path, **kwargs):
        Path(output_path).write_bytes(b"new-short")

    def test_editor_requires_authorization_and_source_relationship(self):
        url = reverse("rerender_short", args=[self.short.pk])
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 403)

        direct_short = Video.objects.create(
            title="Direct", description="Direct", author=self.creator, channel=self.channel,
            thumbnail=SimpleUploadedFile("direct.jpg", b"thumb", content_type="image/jpeg"),
            video_file=SimpleUploadedFile("direct.mp4", b"video", content_type="video/mp4"),
        )
        VideoShort.objects.create(video=direct_short)
        self.client.force_login(self.creator)
        self.assertEqual(self.client.get(reverse("rerender_short", args=[direct_short.pk])).status_code, 400)

    def test_editor_prepopulates_stored_clip_metadata(self):
        self.client.force_login(self.creator)
        response = self.client.get(reverse("rerender_short", args=[self.short.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial["start_seconds"], 10)
        self.assertEqual(response.context["form"].initial["end_seconds"], 40)
        self.assertEqual(response.context["form"].initial["reframing_mode"], VideoShort.ReframingMode.VERTICAL_CENTER)

    @patch("video.services.short_clips._run_ffmpeg", side_effect=fake_ffmpeg.__func__)
    def test_rerender_preserves_video_identity_and_publication_state(self, unused_ffmpeg):
        old_name = self.short.video_file.name
        original_pk = self.short.pk
        rerender_short_from_source(
            short=self.short, start_seconds=20, end_seconds=55,
            reframing_mode=VideoShort.ReframingMode.VERTICAL_RIGHT,
        )
        self.short.refresh_from_db()
        metadata = self.short.short_metadata
        self.assertEqual(self.short.pk, original_pk)
        self.assertEqual(self.short.publication_status, Video.PublicationStatus.PUBLISHED)
        self.assertEqual(self.short.title, "Existing Short")
        self.assertNotEqual(self.short.video_file.name, old_name)
        self.assertEqual(Path(self.short.video_file.path).read_bytes(), b"new-short")
        self.assertFalse(self.short.video_file.storage.exists(old_name))
        self.assertEqual(metadata.source_start_seconds, 20)
        self.assertEqual(metadata.source_end_seconds, 55)
        self.assertEqual(metadata.reframing_mode, VideoShort.ReframingMode.VERTICAL_RIGHT)

    @patch("video.services.short_clips._run_ffmpeg", side_effect=ShortClipError("conversion failed"))
    def test_failed_render_keeps_existing_media_and_metadata(self, unused_ffmpeg):
        old_name = self.short.video_file.name
        with self.assertRaisesMessage(ShortClipError, "conversion failed"):
            rerender_short_from_source(
                short=self.short, start_seconds=20, end_seconds=50,
                reframing_mode=VideoShort.ReframingMode.VERTICAL_LEFT,
            )
        self.short.refresh_from_db()
        metadata = self.short.short_metadata
        self.assertEqual(self.short.video_file.name, old_name)
        self.assertTrue(self.short.video_file.storage.exists(old_name))
        self.assertEqual(metadata.source_start_seconds, 10)
        self.assertEqual(metadata.source_end_seconds, 40)

    @patch("video.services.short_clips._run_ffmpeg", side_effect=fake_ffmpeg.__func__)
    def test_post_rerenders_and_returns_to_existing_video_editor(self, unused_ffmpeg):
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("rerender_short", args=[self.short.pk]),
            {"title": self.short.title, "description": self.short.description, "start_seconds": 15,
             "end_seconds": 45, "reframing_mode": VideoShort.ReframingMode.VERTICAL_LEFT},
        )
        self.assertRedirects(response, reverse("video_edit", args=[self.short.pk]), fetch_redirect_response=False)
        self.short.refresh_from_db()
        self.assertEqual(self.short.short_metadata.source_start_seconds, 15)
