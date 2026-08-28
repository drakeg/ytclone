import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from django.core.files import File
from django.db import transaction

from video.models import Video
from video.shorts_models import VideoShort


class ShortClipError(Exception):
    pass


def _copy_storage_file(field_file, destination):
    field_file.open("rb")
    try:
        shutil.copyfileobj(field_file.file, destination)
    finally:
        field_file.close()


def _vertical_filter(reframing_mode):
    if reframing_mode == VideoShort.ReframingMode.VERTICAL_LEFT:
        crop_x = "0"
    elif reframing_mode == VideoShort.ReframingMode.VERTICAL_RIGHT:
        crop_x = "iw-720"
    else:
        crop_x = "(iw-720)/2"
    return (
        "scale=720:1280:force_original_aspect_ratio=increase,"
        f"crop=720:1280:{crop_x}:(ih-1280)/2,setsar=1"
    )


def _overlay_y(position):
    if position == VideoShort.OverlayPosition.TOP:
        return "h*0.10"
    if position == VideoShort.OverlayPosition.CENTER:
        return "(h-text_h)/2"
    return "h-text_h-h*0.10"


def _validate_clip(start_seconds, end_seconds, reframing_mode, overlay_text="", overlay_position=VideoShort.OverlayPosition.BOTTOM):
    if start_seconds < 0 or end_seconds <= start_seconds:
        raise ShortClipError("Choose a valid start and end time.")
    if end_seconds - start_seconds > 180:
        raise ShortClipError("Short clips must be 180 seconds or shorter.")
    valid_reframing_modes = {choice for choice, unused_label in VideoShort.ReframingMode.choices}
    if reframing_mode not in valid_reframing_modes:
        raise ShortClipError("Choose a valid Short framing option.")
    if len(overlay_text or "") > 120:
        raise ShortClipError("Short overlay text must be 120 characters or shorter.")
    valid_overlay_positions = {choice for choice, unused_label in VideoShort.OverlayPosition.choices}
    if overlay_position not in valid_overlay_positions:
        raise ShortClipError("Choose a valid text overlay position.")


def _run_ffmpeg(
    source_path,
    output_path,
    *,
    start_seconds,
    end_seconds,
    reframing_mode,
    overlay_text="",
    overlay_position=VideoShort.OverlayPosition.BOTTOM,
):
    duration = end_seconds - start_seconds
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", str(start_seconds), "-i", source_path, "-t", str(duration),
    ]
    filters = []
    if reframing_mode != VideoShort.ReframingMode.ORIGINAL:
        filters.append(_vertical_filter(reframing_mode))

    text_file = None
    try:
        if overlay_text:
            text_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", encoding="utf-8")
            text_file.write(overlay_text)
            text_file.flush()
            filters.append(
                "drawtext="
                "fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"textfile={text_file.name}:"
                "fontcolor=white:fontsize=48:"
                "box=1:boxcolor=black@0.55:boxborderw=18:"
                f"x=(w-text_w)/2:y={_overlay_y(overlay_position)}"
            )
        if filters:
            command.extend(["-vf", ",".join(filters)])
        command.extend([
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-movflags", "+faststart", output_path,
        ])
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
    except FileNotFoundError as error:
        raise ShortClipError("FFmpeg is not installed on this server.") from error
    except subprocess.TimeoutExpired as error:
        raise ShortClipError("Short creation took too long and was stopped.") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip()
        raise ShortClipError(
            f"FFmpeg could not create the Short{': ' + detail[:300] if detail else '.'}"
        ) from error
    finally:
        if text_file is not None:
            text_file.close()


def create_short_from_video(
    *, source_video, creator, title, description, start_seconds, end_seconds,
    reframing_mode=VideoShort.ReframingMode.ORIGINAL,
    overlay_text="", overlay_position=VideoShort.OverlayPosition.BOTTOM,
):
    if hasattr(source_video, "short_metadata"):
        raise ShortClipError("Create a Short from a standard video, not another Short.")
    overlay_text = (overlay_text or "").strip()
    _validate_clip(start_seconds, end_seconds, reframing_mode, overlay_text, overlay_position)

    source_suffix = Path(source_video.video_file.name).suffix or ".mp4"
    saved_video_name = None
    saved_thumbnail_name = None

    with tempfile.NamedTemporaryFile(suffix=source_suffix) as source_temp, tempfile.NamedTemporaryFile(suffix=".mp4") as output_temp:
        _copy_storage_file(source_video.video_file, source_temp)
        source_temp.flush()
        _run_ffmpeg(
            source_temp.name, output_temp.name,
            start_seconds=start_seconds, end_seconds=end_seconds,
            reframing_mode=reframing_mode,
            overlay_text=overlay_text, overlay_position=overlay_position,
        )
        output_temp.flush()

        try:
            with transaction.atomic():
                short = Video(
                    title=title.strip(), description=(description or "").strip(),
                    author=creator, channel=source_video.channel, category=source_video.category,
                    publication_status=Video.PublicationStatus.DRAFT, audience=Video.Audience.EVERYONE,
                )
                output_temp.seek(0)
                generated_name = f"derived-short-{uuid.uuid4().hex}.mp4"
                short.video_file.save(generated_name, File(output_temp), save=False)
                saved_video_name = short.video_file.name

                with tempfile.NamedTemporaryFile(suffix=Path(source_video.thumbnail.name).suffix or ".jpg") as thumbnail_temp:
                    _copy_storage_file(source_video.thumbnail, thumbnail_temp)
                    thumbnail_temp.flush()
                    thumbnail_temp.seek(0)
                    thumbnail_name = f"derived-short-{uuid.uuid4().hex}{Path(source_video.thumbnail.name).suffix or '.jpg'}"
                    short.thumbnail.save(thumbnail_name, File(thumbnail_temp), save=False)
                    saved_thumbnail_name = short.thumbnail.name

                short.save()
                VideoShort.objects.create(
                    video=short, source_video=source_video,
                    source_start_seconds=start_seconds, source_end_seconds=end_seconds,
                    reframing_mode=reframing_mode,
                    overlay_text=overlay_text, overlay_position=overlay_position,
                )
                short.tags.set(source_video.tags.all())
                return short
        except Exception:
            if saved_video_name:
                source_video.video_file.storage.delete(saved_video_name)
            if saved_thumbnail_name:
                source_video.thumbnail.storage.delete(saved_thumbnail_name)
            raise


def rerender_short_from_source(
    *, short, start_seconds, end_seconds, reframing_mode,
    overlay_text="", overlay_position=VideoShort.OverlayPosition.BOTTOM,
):
    try:
        metadata = short.short_metadata
    except VideoShort.DoesNotExist as error:
        raise ShortClipError("Only Shorts can be re-rendered.") from error
    if not metadata.source_video_id:
        raise ShortClipError("This Short was not generated from a source video.")

    overlay_text = (overlay_text or "").strip()
    _validate_clip(start_seconds, end_seconds, reframing_mode, overlay_text, overlay_position)
    source_video = metadata.source_video
    source_suffix = Path(source_video.video_file.name).suffix or ".mp4"
    storage = short.video_file.storage
    old_video_name = short.video_file.name
    new_video_name = None

    with tempfile.NamedTemporaryFile(suffix=source_suffix) as source_temp, tempfile.NamedTemporaryFile(suffix=".mp4") as output_temp:
        _copy_storage_file(source_video.video_file, source_temp)
        source_temp.flush()
        _run_ffmpeg(
            source_temp.name, output_temp.name,
            start_seconds=start_seconds, end_seconds=end_seconds,
            reframing_mode=reframing_mode,
            overlay_text=overlay_text, overlay_position=overlay_position,
        )
        output_temp.flush()

        try:
            with transaction.atomic():
                output_temp.seek(0)
                generated_name = f"derived-short-{uuid.uuid4().hex}.mp4"
                short.video_file.save(generated_name, File(output_temp), save=False)
                new_video_name = short.video_file.name
                short.save(update_fields=["video_file"])
                metadata.source_start_seconds = start_seconds
                metadata.source_end_seconds = end_seconds
                metadata.reframing_mode = reframing_mode
                metadata.overlay_text = overlay_text
                metadata.overlay_position = overlay_position
                metadata.save(update_fields=[
                    "source_start_seconds", "source_end_seconds", "reframing_mode",
                    "overlay_text", "overlay_position",
                ])
        except Exception:
            if new_video_name:
                storage.delete(new_video_name)
            raise

    if old_video_name and old_video_name != new_video_name:
        storage.delete(old_video_name)
    return short
