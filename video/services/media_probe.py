import json
import shutil
import subprocess
import tempfile
from pathlib import Path


SHORT_MAX_SECONDS = 180


class MediaProbeError(Exception):
    pass


def _rotation_from_stream(stream):
    tags = stream.get("tags") or {}
    try:
        tag_rotation = int(float(tags.get("rotate", 0)))
    except (TypeError, ValueError):
        tag_rotation = 0
    if tag_rotation:
        return tag_rotation % 360

    for side_data in stream.get("side_data_list") or []:
        try:
            rotation = int(float(side_data.get("rotation", 0)))
        except (TypeError, ValueError):
            rotation = 0
        if rotation:
            return rotation % 360
    return 0


def parse_probe_payload(payload):
    streams = payload.get("streams") or []
    if not streams:
        raise MediaProbeError("No video stream was found.")
    stream = streams[0]
    try:
        width = int(stream["width"])
        height = int(stream["height"])
    except (KeyError, TypeError, ValueError) as error:
        raise MediaProbeError("Video dimensions could not be determined.") from error

    duration_value = stream.get("duration")
    if duration_value in (None, "N/A"):
        duration_value = (payload.get("format") or {}).get("duration")
    try:
        duration = float(duration_value)
    except (TypeError, ValueError) as error:
        raise MediaProbeError("Video duration could not be determined.") from error
    if duration <= 0:
        raise MediaProbeError("Video duration could not be determined.")

    rotation = _rotation_from_stream(stream)
    if rotation in {90, 270}:
        width, height = height, width

    return {
        "width": width,
        "height": height,
        "duration_seconds": duration,
        "rotation": rotation,
    }


def probe_video_path(path):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,duration:stream_tags=rotate:stream_side_data=rotation:format=duration",
        "-of",
        "json",
        str(path),
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as error:
        raise MediaProbeError("FFprobe is not installed on this server.") from error
    except subprocess.TimeoutExpired as error:
        raise MediaProbeError("Video inspection took too long.") from error
    except subprocess.CalledProcessError as error:
        raise MediaProbeError("Video metadata could not be inspected.") from error

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise MediaProbeError("FFprobe returned invalid metadata.") from error
    return parse_probe_payload(payload)


def probe_uploaded_video(uploaded_file):
    original_position = None
    try:
        original_position = uploaded_file.tell()
    except (AttributeError, OSError):
        pass

    suffix = Path(getattr(uploaded_file, "name", "")).suffix or ".video"
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix) as temp_file:
            try:
                uploaded_file.seek(0)
            except (AttributeError, OSError):
                pass
            shutil.copyfileobj(uploaded_file, temp_file)
            temp_file.flush()
            return probe_video_path(temp_file.name)
    finally:
        if original_position is not None:
            try:
                uploaded_file.seek(original_position)
            except (AttributeError, OSError):
                pass


def should_auto_classify_as_short(probe):
    if not probe:
        return False
    return (
        probe["height"] >= probe["width"]
        and probe["duration_seconds"] <= SHORT_MAX_SECONDS
    )
