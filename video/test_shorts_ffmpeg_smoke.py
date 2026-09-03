import shutil
import subprocess
import tempfile
from pathlib import Path

from django.test import SimpleTestCase, skipUnlessDBFeature
from unittest import skipUnless

from .services.short_clips import _run_ffmpeg, _run_thumbnail_ffmpeg
from .shorts_models import VideoShort


FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None


@skipUnless(FFMPEG_AVAILABLE, "FFmpeg is required for real-binary smoke coverage")
class ShortsRealFfmpegSmokeTests(SimpleTestCase):
    def _create_source(self, path):
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=blue:s=360x640:d=1:r=10",
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_real_ffmpeg_renders_overlay_clip_and_thumbnail(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source = directory / "source.mp4"
            output = directory / "short.mp4"
            thumbnail = directory / "thumbnail.jpg"
            self._create_source(source)

            _run_ffmpeg(
                str(source),
                str(output),
                start_seconds=0,
                end_seconds=0.5,
                reframing_mode=VideoShort.ReframingMode.ORIGINAL,
                overlay_text="Smoke test",
                overlay_position=VideoShort.OverlayPosition.BOTTOM,
            )
            _run_thumbnail_ffmpeg(
                str(source),
                str(thumbnail),
                frame_seconds=0.25,
            )

            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 0)
            self.assertTrue(thumbnail.exists())
            self.assertGreater(thumbnail.stat().st_size, 0)
