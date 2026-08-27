import base64
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from .forms import VideoEditForm, VideoUploadForm
from .models import Channel, Video
from .services.media_probe import (
    MediaProbeError,
    parse_probe_payload,
    probe_uploaded_video,
    should_auto_classify_as_short,
)
from .shorts_models import VideoShort


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class ShortsAutoDetectionTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.media_dir.cleanup)
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.channel = Channel.objects.create(
            owner=self.creator,
            name="Auto Detect Channel",
            description="",
        )

    def files(self):
        return {
            "thumbnail": SimpleUploadedFile("thumb.png", PNG_1X1, content_type="image/png"),
            "video_file": SimpleUploadedFile("clip.mp4", b"fake-video-data", content_type="video/mp4"),
        }

    def payload(self, content_format="auto"):
        return {
            "title": "Detected upload",
            "description": "",
            "category": "",
            "channel": str(self.channel.pk),
            "publication_status": Video.PublicationStatus.PUBLISHED,
            "audience": Video.Audience.EVERYONE,
            "publish_at": "",
            "public_release_at": "",
            "content_format": content_format,
            "tags": "",
            "chapters": "",
        }

    def save_with_probe(self, probe, *, content_format="auto"):
        with patch("video.forms.probe_uploaded_video", return_value=probe):
            form = VideoUploadForm(
                self.payload(content_format),
                files=self.files(),
                user=self.creator,
            )
            self.assertTrue(form.is_valid(), form.errors)
            return form.save()

    def test_new_upload_defaults_to_auto_detect(self):
        form = VideoUploadForm(user=self.creator)
        self.assertEqual(form.fields["content_format"].initial, "auto")
        choices = dict(form.fields["content_format"].choices)
        self.assertEqual(choices["auto"], "Auto-detect")

    def test_auto_detect_marks_short_portrait_and_square_media(self):
        portrait = self.save_with_probe(
            {"width": 1080, "height": 1920, "duration_seconds": 45, "rotation": 0}
        )
        square = self.save_with_probe(
            {"width": 1080, "height": 1080, "duration_seconds": 180, "rotation": 0}
        )
        self.assertTrue(VideoShort.objects.filter(video=portrait).exists())
        self.assertTrue(VideoShort.objects.filter(video=square).exists())

    def test_auto_detect_keeps_landscape_or_long_vertical_as_standard_video(self):
        landscape = self.save_with_probe(
            {"width": 1920, "height": 1080, "duration_seconds": 30, "rotation": 0}
        )
        long_portrait = self.save_with_probe(
            {"width": 1080, "height": 1920, "duration_seconds": 181, "rotation": 0}
        )
        self.assertFalse(VideoShort.objects.filter(video=landscape).exists())
        self.assertFalse(VideoShort.objects.filter(video=long_portrait).exists())

    def test_explicit_format_overrides_auto_detection(self):
        forced_video = self.save_with_probe(
            {"width": 1080, "height": 1920, "duration_seconds": 20, "rotation": 0},
            content_format="video",
        )
        forced_short = self.save_with_probe(
            {"width": 1920, "height": 1080, "duration_seconds": 600, "rotation": 0},
            content_format="short",
        )
        self.assertFalse(VideoShort.objects.filter(video=forced_video).exists())
        self.assertTrue(VideoShort.objects.filter(video=forced_short).exists())

    def test_probe_failure_falls_back_to_standard_without_blocking_upload(self):
        with patch(
            "video.forms.probe_uploaded_video",
            side_effect=MediaProbeError("cannot inspect"),
        ):
            form = VideoUploadForm(self.payload(), files=self.files(), user=self.creator)
            self.assertTrue(form.is_valid(), form.errors)
            video = form.save()
        self.assertFalse(VideoShort.objects.filter(video=video).exists())

    def test_edit_without_replacement_preserves_existing_format(self):
        video = Video.objects.create(
            title="Existing Short",
            description="",
            thumbnail="videos/thumbnails/existing.png",
            video_file="videos/files/existing.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=video)
        payload = self.payload("auto")
        payload["title"] = video.title
        form = VideoEditForm(payload, instance=video, user=self.creator)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertTrue(VideoShort.objects.filter(video=video).exists())

    def test_rotation_metadata_is_applied_before_orientation_classification(self):
        probe = parse_probe_payload(
            {
                "streams": [
                    {
                        "width": 1920,
                        "height": 1080,
                        "duration": "30.0",
                        "side_data_list": [{"rotation": -90}],
                    }
                ],
                "format": {"duration": "30.0"},
            }
        )
        self.assertEqual((probe["width"], probe["height"]), (1080, 1920))
        self.assertTrue(should_auto_classify_as_short(probe))

    def test_probe_uploaded_video_restores_file_position(self):
        upload = SimpleUploadedFile("position.mp4", b"0123456789", content_type="video/mp4")
        upload.seek(4)
        with patch(
            "video.services.media_probe.probe_video_path",
            return_value={"width": 1080, "height": 1920, "duration_seconds": 10, "rotation": 0},
        ):
            result = probe_uploaded_video(upload)
        self.assertEqual(result["duration_seconds"], 10)
        self.assertEqual(upload.tell(), 4)
