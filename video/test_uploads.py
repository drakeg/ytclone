from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from .forms import VideoUploadForm
from .models import Category, Channel


class VideoUploadValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="uploader", password="password123")
        self.category = Category.objects.create(
            name="General",
            description="General videos",
            thumbnail="categories/thumbnails/general.jpg",
        )
        self.channel = Channel.objects.create(
            name="Uploader channel",
            description="Uploads",
            thumbnail="channels/uploader.jpg",
            owner=self.user,
        )

    def make_thumbnail(self, name="thumbnail.jpg", content_type="image/jpeg"):
        image_bytes = BytesIO()
        Image.new("RGB", (8, 8)).save(image_bytes, format="JPEG")
        return SimpleUploadedFile(name, image_bytes.getvalue(), content_type=content_type)

    def make_video(self, name="video.mp4", content_type="video/mp4", content=b"video"):
        return SimpleUploadedFile(name, content, content_type=content_type)

    def form_data(self):
        return {
            "title": "Upload test",
            "description": "Testing upload validation",
            "category": self.category.pk,
            "channel": self.channel.pk,
        }

    def test_supported_uploads_are_accepted(self):
        form = VideoUploadForm(
            user=self.user,
            data=self.form_data(),
            files={
                "thumbnail": self.make_thumbnail(),
                "video_file": self.make_video(),
            },
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_unsupported_video_extension_is_rejected(self):
        form = VideoUploadForm(
            user=self.user,
            data=self.form_data(),
            files={
                "thumbnail": self.make_thumbnail(),
                "video_file": self.make_video(name="video.exe"),
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("video_file", form.errors)

    def test_mismatched_video_content_type_is_rejected(self):
        form = VideoUploadForm(
            user=self.user,
            data=self.form_data(),
            files={
                "thumbnail": self.make_thumbnail(),
                "video_file": self.make_video(content_type="application/octet-stream"),
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("video_file", form.errors)

    @override_settings(MAX_VIDEO_UPLOAD_SIZE=4, MAX_VIDEO_UPLOAD_MB=0)
    def test_oversized_video_is_rejected(self):
        form = VideoUploadForm(
            user=self.user,
            data=self.form_data(),
            files={
                "thumbnail": self.make_thumbnail(),
                "video_file": self.make_video(content=b"12345"),
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("video_file", form.errors)

    def test_unsupported_thumbnail_extension_is_rejected(self):
        form = VideoUploadForm(
            user=self.user,
            data=self.form_data(),
            files={
                "thumbnail": self.make_thumbnail(name="thumbnail.bmp", content_type="image/bmp"),
                "video_file": self.make_video(),
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("thumbnail", form.errors)
