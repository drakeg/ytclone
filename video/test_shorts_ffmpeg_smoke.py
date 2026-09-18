import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch
from unittest import skipUnless

from django.test import SimpleTestCase

from .services.short_clips import _run_ffmpeg, _run_thumbnail_ffmpeg
from .shorts_models import VideoShort


def _ffmpeg_component_available(output, component):
    return any(component in line.split() for line in output.splitlines())


def _ffmpeg_supports_smoke_test():
    if shutil.which("ffmpeg") is None:
        return False

    try:
        filters = subprocess.run(
            ["ffmpeg", "-hide_banner", "-filters"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        encoders = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False

    filter_output = f"{filters.stdout}\n{filters.stderr}"
    encoder_output = f"{encoders.stdout}\n{encoders.stderr}"
    return (
        _ffmpeg_component_available(filter_output, "drawtext")
        and _ffmpeg_component_available(encoder_output, "libx264")
        and _ffmpeg_component_available(encoder_output, "aac")
    )


FFMPEG_SMOKE_SUPPORTED = _ffmpeg_supports_smoke_test()


class FfmpegCapabilityDetectionTests(SimpleTestCase):
    @patch("video.test_shorts_ffmpeg_smoke.shutil.which", return_value=None)
    def test_reports_unsupported_when_ffmpeg_is_unavailable(self, _which):
        self.assertFalse(_ffmpeg_supports_smoke_test())

    @patch("video.test_shorts_ffmpeg_smoke.subprocess.run")
    @patch("video.test_shorts_ffmpeg_smoke.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_reports_supported_when_required_components_are_available(self, _which, run):
        run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=" T.. drawtext V->V Draw text", stderr=""),
            subprocess.CompletedProcess(
                [],
                0,
                stdout=" V....D libx264 H.264\n A....D aac AAC",
                stderr="",
            ),
        ]

        self.assertTrue(_ffmpeg_supports_smoke_test())

    @patch("video.test_shorts_ffmpeg_smoke.subprocess.run")
    @patch("video.test_shorts_ffmpeg_smoke.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_reports_unsupported_when_drawtext_is_unavailable(self, _which, run):
        run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=" T.. scale V->V Scale video", stderr=""),
            subprocess.CompletedProcess(
                [],
                0,
                stdout=" V....D libx264 H.264\n A....D aac AAC",
                stderr="",
            ),
        ]

        self.assertFalse(_ffmpeg_supports_smoke_test())

    @patch("video.test_shorts_ffmpeg_smoke.subprocess.run")
    @patch("video.test_shorts_ffmpeg_smoke.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_reports_unsupported_when_capability_probe_fails(self, _which, run):
        run.side_effect = subprocess.TimeoutExpired("ffmpeg", 10)

        self.assertFalse(_ffmpeg_supports_smoke_test())


@skipUnless(
    FFMPEG_SMOKE_SUPPORTED,
    "FFmpeg with drawtext, libx264, and AAC is required for real-binary smoke coverage",
)
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
