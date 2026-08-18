from django.test import SimpleTestCase

from .forms import VideoUploadForm


class VideoUploadFilePickerTests(SimpleTestCase):
    def test_video_file_widget_has_no_accept_filter(self):
        widget = VideoUploadForm.base_fields["video_file"].widget

        self.assertNotIn("accept", widget.attrs)

    def test_thumbnail_widget_keeps_image_accept_filter(self):
        widget = VideoUploadForm.base_fields["thumbnail"].widget

        self.assertEqual(widget.attrs.get("accept"), "image/jpeg,image/png,image/webp")
