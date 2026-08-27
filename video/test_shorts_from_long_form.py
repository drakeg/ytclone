import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .metadata_models import Tag
from .models import Channel, Video
from .services.short_clips import ShortClipError, create_short_from_video
from .shorts_models import VideoShort


class ShortsFromLongFormTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.media_dir.cleanup)

        self.creator = User.objects.create_user(username="creator", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Clip Channel", description="")
        self.source = Video.objects.create(
            title="Long Source Video",
            description="Source description",
            thumbnail=SimpleUploadedFile("source.jpg", b"fake-thumbnail", content_type="image/jpeg"),
            video_file=SimpleUploadedFile("source.mp4", b"fake-video", content_type="video/mp4"),
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        self.tag = Tag.objects.create(name="travel")
        self.source.tags.add(self.tag)

    @staticmethod
    def fake_ffmpeg(source_path, output_path, **kwargs):
        Path(output_path).write_bytes(b"generated-short")

    def test_clip_form_page_is_creator_only_and_rejects_short_source(self):
        url = reverse("create_short_from_long_form", args=[self.source.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 403)

        VideoShort.objects.create(video=self.source)
        self.client.force_login(self.creator)
        self.assertEqual(self.client.get(url).status_code, 400)

    def test_clip_page_renders_for_creator_and_library_links_to_it(self):
        self.client.force_login(self.creator)
        response = self.client.get(reverse("create_short_from_long_form", args=[self.source.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create a Short from Long Source Video")

        library = self.client.get(reverse("creator_video_list"))
        self.assertContains(library, reverse("create_short_from_long_form", args=[self.source.pk]))

    def test_invalid_clip_ranges_are_rejected_without_creating_video(self):
        self.client.force_login(self.creator)
        url = reverse("create_short_from_long_form", args=[self.source.pk])
        before = Video.objects.count()
        response = self.client.post(url, {"title": "Bad clip", "description": "", "start_seconds": 10, "end_seconds": 10})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "End time must be after the start time")
        self.assertEqual(Video.objects.count(), before)

        response = self.client.post(url, {"title": "Too long", "description": "", "start_seconds": 0, "end_seconds": 181})
        self.assertContains(response, "180 seconds or shorter")
        self.assertEqual(Video.objects.count(), before)

    @patch("video.services.short_clips._run_ffmpeg", side_effect=fake_ffmpeg.__func__)
    def test_service_creates_draft_short_with_source_context(self, unused_ffmpeg):
        short = create_short_from_video(
            source_video=self.source,
            creator=self.creator,
            title="My Derived Short",
            description="A selected moment",
            start_seconds=12,
            end_seconds=42,
        )
        self.assertEqual(short.publication_status, Video.PublicationStatus.DRAFT)
        self.assertEqual(short.channel, self.channel)
        self.assertEqual(list(short.tags.values_list("name", flat=True)), ["travel"])
        self.assertNotEqual(short.video_file.name, self.source.video_file.name)
        self.assertNotEqual(short.thumbnail.name, self.source.thumbnail.name)

        metadata = VideoShort.objects.get(video=short)
        self.assertEqual(metadata.source_video, self.source)
        self.assertEqual(metadata.source_start_seconds, 12)
        self.assertEqual(metadata.source_end_seconds, 42)
        self.assertTrue(Path(short.video_file.path).exists())
        self.assertEqual(Path(short.video_file.path).read_bytes(), b"generated-short")

    @patch("video.services.short_clips._run_ffmpeg", side_effect=ShortClipError("conversion failed"))
    def test_failed_conversion_leaves_no_partial_short(self, unused_ffmpeg):
        before = Video.objects.count()
        with self.assertRaisesMessage(ShortClipError, "conversion failed"):
            create_short_from_video(
                source_video=self.source,
                creator=self.creator,
                title="Failed Short",
                description="",
                start_seconds=0,
                end_seconds=30,
            )
        self.assertEqual(Video.objects.count(), before)
        self.assertFalse(VideoShort.objects.filter(source_video=self.source).exists())

    @patch("video.services.short_clips._run_ffmpeg", side_effect=fake_ffmpeg.__func__)
    def test_post_creates_draft_then_redirects_to_normal_editor(self, unused_ffmpeg):
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("create_short_from_long_form", args=[self.source.pk]),
            {"title": "Web Created Short", "description": "Review me", "start_seconds": 5, "end_seconds": 25},
        )
        short = Video.objects.get(title="Web Created Short")
        self.assertRedirects(response, reverse("video_edit", args=[short.pk]), fetch_redirect_response=False)
        self.assertTrue(VideoShort.objects.filter(video=short, source_video=self.source).exists())
        self.assertEqual(short.publication_status, Video.PublicationStatus.DRAFT)
