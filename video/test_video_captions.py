from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .forms import VideoEditForm
from .models import Category, Channel, Video
from .services.captions import CaptionValidationError, validate_webvtt_upload


class VideoCaptionTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="caption-creator", password="pw")
        self.channel = Channel.objects.create(name="Caption channel", description="", owner=self.creator)
        self.category = Category.objects.create(name="Caption category")
        self.video = Video.objects.create(
            title="Captioned video",
            description="Description",
            thumbnail="videos/thumbnails/thumb.jpg",
            video_file="videos/files/video.mp4",
            author=self.creator,
            channel=self.channel,
            category=self.category,
        )

    def caption(self, content=b"WEBVTT\n\n00:00.000 --> 00:02.000\nHello\n", name="captions.vtt"):
        return SimpleUploadedFile(name, content, content_type="text/vtt")

    def edit_data(self):
        return {
            "title": self.video.title,
            "description": self.video.description,
            "category": self.category.pk,
            "channel": self.channel.pk,
            "publication_status": Video.PublicationStatus.PUBLISHED,
            "audience": Video.Audience.EVERYONE,
            "content_format": "video",
        }

    def test_validator_accepts_utf8_webvtt_and_restores_pointer(self):
        caption = self.caption()
        self.assertIs(validate_webvtt_upload(caption), caption)
        self.assertEqual(caption.tell(), 0)

    def test_validator_rejects_wrong_extension_and_header(self):
        with self.assertRaises(CaptionValidationError):
            validate_webvtt_upload(self.caption(name="captions.txt"))
        with self.assertRaises(CaptionValidationError):
            validate_webvtt_upload(self.caption(content=b"00:00.000 --> 00:02.000\nHello\n"))

    def test_edit_form_accepts_caption_file(self):
        form = VideoEditForm(self.edit_data(), {"captions_file": self.caption()}, instance=self.video, user=self.creator)
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        self.assertTrue(saved.captions_file.name.endswith(".vtt"))

    def test_edit_form_rejects_invalid_caption_file(self):
        form = VideoEditForm(self.edit_data(), {"captions_file": self.caption(content=b"not webvtt")}, instance=self.video, user=self.creator)
        self.assertFalse(form.is_valid())
        self.assertIn("captions_file", form.errors)

    def test_watch_page_renders_native_caption_track(self):
        self.video.captions_file = "videos/captions/captions.vtt"
        self.video.save(update_fields=["captions_file"])
        response = self.client.get(reverse("video_detail", kwargs={"pk": self.video.pk}))
        self.assertContains(response, 'kind="captions"')
        self.assertContains(response, 'srclang="en"')
        self.assertContains(response, "/media/videos/captions/captions.vtt")

    def test_watch_page_omits_track_without_caption(self):
        response = self.client.get(reverse("video_detail", kwargs={"pk": self.video.pk}))
        self.assertNotContains(response, 'kind="captions"')

    def test_edit_page_exposes_optional_webvtt_input(self):
        self.client.force_login(self.creator)
        response = self.client.get(reverse("video_edit", kwargs={"pk": self.video.pk}))
        self.assertContains(response, "Optional English WebVTT")
        self.assertContains(response, 'accept=".vtt,text/vtt"')
