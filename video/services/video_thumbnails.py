import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageStat

from .media_probe import MediaProbeError, probe_video_path


AUTO_SAMPLE_FRACTIONS = (0.15, 0.30, 0.45, 0.60, 0.75, 0.90)


class VideoThumbnailError(Exception):
    pass


def _copy_uploaded_file(uploaded_file, destination):
    original_position = None
    try:
        original_position = uploaded_file.tell()
    except (AttributeError, OSError):
        pass

    try:
        try:
            uploaded_file.seek(0)
        except (AttributeError, OSError):
            pass
        shutil.copyfileobj(uploaded_file, destination)
    finally:
        if original_position is not None:
            try:
                uploaded_file.seek(original_position)
            except (AttributeError, OSError):
                pass


def _extract_frame(source_path, output_path, frame_seconds):
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        str(frame_seconds),
        "-i",
        str(source_path),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(output_path),
    ]
    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError as error:
        raise VideoThumbnailError("FFmpeg is not installed on this server.") from error
    except subprocess.TimeoutExpired as error:
        raise VideoThumbnailError("Thumbnail generation took too long and was stopped.") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip()
        raise VideoThumbnailError(
            f"FFmpeg could not generate a thumbnail{': ' + detail[:300] if detail else '.'}"
        ) from error


def _frame_score(path):
    with Image.open(path) as image:
        grayscale = image.convert("L")
        stats = ImageStat.Stat(grayscale)
        brightness = stats.mean[0]
        contrast = stats.stddev[0]

    score = contrast * 2.0 - abs(brightness - 128.0) * 0.20
    if brightness < 40:
        score -= (40 - brightness) * 4.0
    elif brightness > 225:
        score -= (brightness - 225) * 3.0
    if contrast < 12:
        score -= (12 - contrast) * 5.0
    return score


def _probe_duration(source_path):
    try:
        return probe_video_path(source_path)["duration_seconds"]
    except MediaProbeError as error:
        raise VideoThumbnailError(str(error)) from error


def _generated_file(frame_bytes):
    return ContentFile(
        frame_bytes,
        name=f"video-thumbnail-{uuid.uuid4().hex}.jpg",
    )


def _selected_frame(source_path, frame_seconds, duration_seconds):
    if frame_seconds < 0 or frame_seconds > duration_seconds:
        raise VideoThumbnailError("The selected thumbnail frame is outside the video duration.")
    with tempfile.NamedTemporaryFile(suffix=".jpg") as output:
        _extract_frame(source_path, output.name, frame_seconds)
        output.seek(0)
        return output.read()


def _automatic_frame(source_path, duration_seconds):
    best = None
    for fraction in AUTO_SAMPLE_FRACTIONS:
        frame_seconds = duration_seconds * fraction
        with tempfile.NamedTemporaryFile(suffix=".jpg") as output:
            try:
                _extract_frame(source_path, output.name, frame_seconds)
                score = _frame_score(output.name)
            except VideoThumbnailError:
                continue
            output.seek(0)
            candidate = (score, output.read())
            if best is None or candidate[0] > best[0]:
                best = candidate

    if best is None:
        raise VideoThumbnailError("VideoShare could not find a usable frame for the thumbnail.")
    return best[1]


def generate_thumbnail_for_upload(uploaded_file, *, mode, frame_seconds=None):
    if mode == "custom":
        raise VideoThumbnailError("Custom thumbnail mode does not generate a video frame.")

    suffix = Path(getattr(uploaded_file, "name", "")).suffix or ".video"
    with tempfile.NamedTemporaryFile(suffix=suffix) as source:
        _copy_uploaded_file(uploaded_file, source)
        source.flush()
        duration_seconds = _probe_duration(source.name)

        if mode == "frame":
            if frame_seconds is None:
                raise VideoThumbnailError("Choose a frame from the video before uploading.")
            frame_bytes = _selected_frame(source.name, frame_seconds, duration_seconds)
        elif mode == "auto":
            frame_bytes = _automatic_frame(source.name, duration_seconds)
        else:
            raise VideoThumbnailError("Choose a valid thumbnail option.")

    return _generated_file(frame_bytes)
