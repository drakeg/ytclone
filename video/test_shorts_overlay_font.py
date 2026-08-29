import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from .services.short_clips import _run_ffmpeg
from .shorts_models import VideoShort


class ShortsOverlayFontTests(SimpleTestCase):
    @patch("video.services.short_clips.subprocess.run")
    def test_overlay_uses_fontconfig_name_instead_of_linux_absolute_path(self, run):
        with tempfile.NamedTemporaryFile(suffix=".mp4") as source, tempfile.NamedTemporaryFile(suffix=".mp4") as output:
            _run_ffmpeg(
                source.name,
                output.name,
                start_seconds=0,
                end_seconds=10,
                reframing_mode=VideoShort.ReframingMode.VERTICAL_CENTER,
                overlay_text="Portable overlay",
                overlay_position=VideoShort.OverlayPosition.BOTTOM,
            )

        command = run.call_args.args[0]
        filter_value = command[command.index("-vf") + 1]
        self.assertIn("drawtext=font='DejaVu Sans':fontstyle=Bold:", filter_value)
        self.assertNotIn("fontfile=/usr/share/fonts", filter_value)
        self.assertIn("textfile=", filter_value)

    @patch("video.services.short_clips.subprocess.run")
    def test_no_overlay_does_not_add_drawtext_filter(self, run):
        with tempfile.NamedTemporaryFile(suffix=".mp4") as source, tempfile.NamedTemporaryFile(suffix=".mp4") as output:
            _run_ffmpeg(
                source.name,
                output.name,
                start_seconds=0,
                end_seconds=10,
                reframing_mode=VideoShort.ReframingMode.ORIGINAL,
            )

        command = run.call_args.args[0]
        self.assertNotIn("-vf", command)
