# Video Thumbnail Selection Sprint

## Goal

Remove the requirement for creators to upload a separate thumbnail image for every new video while preserving custom thumbnail uploads.

## User experience

New video uploads support three thumbnail modes:

1. **Automatic** (default) — VideoShare samples several frames from the uploaded video and chooses a usable thumbnail using a lightweight brightness/contrast heuristic.
2. **Choose from video** — the browser previews the selected local video; the creator scrubs to a frame and saves that timestamp for server-side FFmpeg extraction.
3. **Upload custom thumbnail** — preserves the current JPG/PNG/WebP upload and validation path.

Every successfully uploaded video still receives a thumbnail. The change only removes the requirement that the creator provide a separate image file.

## Scope

- Add thumbnail-mode and selected-frame fields to the upload form.
- Make the thumbnail image field optional for new uploads unless custom-thumbnail mode is selected.
- Add a local video preview and current-frame selector to the upload page.
- Generate JPEG thumbnails from the uploaded video with existing FFmpeg/FFprobe availability.
- Sample bounded timestamps for automatic selection and reject obviously dark/flat frames using a lightweight image heuristic.
- Keep existing custom thumbnail extension, MIME-type, and size validation unchanged.
- Preserve compatibility with existing upload POSTs that provide a custom thumbnail but predate the new thumbnail-mode field.
- Add focused form, service, view, and browser-contract tests.

## Acceptance criteria

- A new upload with no thumbnail image succeeds in Automatic mode and receives a generated JPEG thumbnail.
- Automatic mode samples a bounded set of frames rather than scanning the entire video.
- Choose-from-video mode requires a selected timestamp and extracts that frame.
- The selected timestamp must be within the uploaded video's duration and before the exact end of the media.
- Custom mode requires an uploaded thumbnail and uses the existing validation rules.
- The upload page shows a video preview/scrubber only for Choose-from-video mode and shows the image file input only for Custom mode.
- Existing custom-thumbnail upload POSTs remain valid when no thumbnail-mode field is present.
- Existing edit-video thumbnail behavior remains unchanged.
- No external service, AI model, worker, queue, schema migration, or paid dependency is added.

## Architecture

- `video/upload_forms.py` owns the new thumbnail-mode validation while reusing the existing `VideoUploadForm` validation.
- A focused `video/services/video_thumbnails.py` service owns FFprobe/FFmpeg thumbnail generation and frame scoring.
- `video/upload_views.py` asks the service for a generated thumbnail before the `Video` model is saved, so generation failures do not leave a partially-created video row.
- `video/templates/videos/upload_video.html` and `video/static/video/upload_thumbnail_picker.js` provide progressive-enhancement controls using the browser's native video element and object URLs. The server remains authoritative for validation and frame extraction.

## Automatic selection heuristic

Automatic selection samples frames at approximately 15%, 30%, 45%, 60%, 75%, and 90% of the video duration. Each extracted frame is scored using grayscale brightness and contrast. Very dark, washed-out, or nearly flat frames receive strong penalties; the highest-scoring sample is used. This is intentionally lightweight and deterministic so Docker and CI remain fast and no external inference service is required.

## Out of scope

- AI/ML thumbnail ranking or face/object detection.
- Text overlays or thumbnail design tools.
- Background thumbnail jobs.
- Multiple stored candidate thumbnails.
- Replacing the existing edit-video thumbnail workflow in this sprint.
