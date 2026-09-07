from pathlib import Path


MAX_CAPTION_BYTES = 2 * 1024 * 1024


class CaptionValidationError(ValueError):
    pass


def validate_webvtt_upload(uploaded_file):
    if uploaded_file is None:
        return None
    if Path(uploaded_file.name).suffix.lower() != ".vtt":
        raise CaptionValidationError("Use a WebVTT (.vtt) caption file.")
    if uploaded_file.size > MAX_CAPTION_BYTES:
        raise CaptionValidationError("Caption files must be 2 MB or smaller.")

    position = uploaded_file.tell() if hasattr(uploaded_file, "tell") else 0
    try:
        payload = uploaded_file.read()
        if isinstance(payload, str):
            text = payload
        else:
            text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise CaptionValidationError("Caption files must be UTF-8 WebVTT text.") from error
    finally:
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(position)

    if not text.lstrip().startswith("WEBVTT"):
        raise CaptionValidationError("Caption files must begin with a WEBVTT header.")
    return uploaded_file
