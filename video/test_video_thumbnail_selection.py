from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Category, Channel, Video
from .services.video_thumbnails import (
    AUTO_SAMPLE_FRACTIONS,
    VideoThumbnailError,
    generate_thumbnail_for_upload,
)
from .upload_forms import ThumbnailVideoUploadForm


class ThumbnailUploadFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="thumbnail-form", password="password123")
        self.channel = Channel.objects.create(owner=self.user, name="Thumbnail Channel", description="")

    def data(self, **overrides):
        payload = {
            "title": "Thumbnail upload",
            "description": "",
            "channel": self.channel.pk,
            "publication_status": Video.PublicationStatus.DRAFT,
            "content_format": "video",
            "thumbnail_mode": "auto",
        }
        payload.update(overrides)
        return payload

    def video(self):
        return SimpleUploadedFile("video.mp4", b"video", content_type="video/mp4")

    def test_new_upload_defaults_to_automatic_thumbnail_and_image_is_optional(self):
        form = ThumbnailVideoUploadForm(user=self.user)
        self.assertEqual(form.fields["thumbnail_mode"].initial, "auto")
        self.assertFalse(form.fields["thumbnail"].required)

    def test_automatic_thumbnail_does_not_require_image_upload(self):
        form = ThumbnailVideoUploadForm(
            user=self.user,
            data=self.data(),
            files={"video_file": self.video()},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_custom_thumbnail_requires_image_upload(self):
        form = ThumbnailVideoUploadForm(
            user=self.user,
            data=self.data(thumbnail_mode="custom"),
            files={"video_file": self.video()},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("thumbnail", form.errors)

    def test_choose_frame_requires_selected_timestamp(self):
        form = ThumbnailVideoUploadForm(
            user=self.user,
            data=self.data(thumbnail_mode="frame"),
            files={"video_file": self.video()},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("thumbnail_frame_seconds", form.errors)


class VideoThumbnailServiceTests(TestCase):
    def video(self):
        return SimpleUploadedFile("video.mp4", b"video", content_type="video/mp4")

    @patch("video.services.video_thumbnails._frame_score")
    @patch("video.services.video_thumbnails._extract_frame")
    @patch("video.services.video_thumbnails._probe_duration", return_value=100)
    def test_automatic_mode_samples_only_bounded_candidate_frames(self, unused_probe, extract_frame, frame_score):
        frame_score.side_effect = [1, 2, 3, 6, 5, 4]
        thumbnail = generate_thumbnail_for_upload(self.video(), mode="auto")

        self.assertTrue(thumbnail.name.endswith(".jpg"))
        self.assertEqual(extract_frame.call_count, len(AUTO_SAMPLE_FRACTIONS))
        sampled_seconds = [call.args[2] for call in extract_frame.call_args_list]
        self.assertEqual(sampled_seconds, [15, 30, 45, 60, 75, 90])

    @patch("video.services.video_thumbnails._extract_frame")
    @patch("video.services.video_thumbnails._probe_duration", return_value=120)
    def test_selected_frame_uses_requested_timestamp(self, unused_probe, extract_frame):
        generate_thumbnail_for_upload(self.video(), mode="frame", frame_seconds=42.5)
        self.assertEqual(extract_frame.call_count, 1)
        self.assertEqual(extract_frame.call_args.args[2], 42.5)

    @patch("video.services.video_thumbnails._probe_duration", return_value=10)
    def test_selected_frame_rejects_timestamp_outside_video(self, unused_probe):
        with self.assertRaisesRegex(VideoThumbnailError, "outside the video duration"):
            generate_thumbnail_for_upload(self.video(), mode="frame", frame_seconds=12)


class ThumbnailUploadViewTests(TestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

        self.user = User.objects.create_user(username="thumbnail-view", password="password123")
        self.category = Category.objects.create(name="General", description="")
        self.channel = Channel.objects.create(owner=self.user, name="View Channel", description="")
        self.client.login(username="thumbnail-view", password="password123")

    def payload(self):
        return {
            "title": "Generated thumbnail video",
            "description": "",
            "category": self.category.pk,
            "channel": self.channel.pk,
            "publication_status": Video.PublicationStatus.DRAFT,
            "content_format": "video",
            "thumbnail_mode": "auto",
            "video_file": SimpleUploadedFile("video.mp4", b"video", content_type="video/mp4"),
        }

    @patch("video.upload_views.generate_thumbnail_for_upload")
    def test_upload_generates_thumbnail_when_no_custom_image_is_supplied(self, generate_thumbnail):
        generate_thumbnail.return_value = ContentFile(b"generated-thumbnail", name="generated.jpg")
        response = self.client.post(reverse("upload"), self.payload())

        self.assertEqual(response.status_code, 302)
        video = Video.objects.get(title="Generated thumbnail video")
        self.assertTrue(video.thumbnail.name.startswith("videos/thumbnails/generated"))
        generate_thumbnail.assert_called_once()

    def test_upload_page_exposes_all_thumbnail_modes_and_frame_picker_controller(self):
        response = self.client.get(reverse("upload"))
        self.assertContains(response, "Automatically select a frame")
        self.assertContains(response, "Choose a frame from the video")
        self.assertContains(response, "Upload a custom thumbnail")
        self.assertContains(response, "video/upload_thumbnail_picker.js")
