# Video Captions Sprint

## Goal
Improve accessibility and watch usability by letting creators attach a WebVTT caption file to standard videos and exposing it through the native HTML video player's caption controls.

## Scope
- Add one optional English WebVTT caption file per video.
- Accept caption upload and replacement from existing video upload/edit flows.
- Validate the uploaded file as bounded UTF-8 WebVTT before persistence.
- Render the caption as a native `<track kind="captions">` on standard-video watch pages.
- Keep caption media private/visibility-bound through the parent video's existing access rules.
- Removing the caption from edit is supported explicitly.

## Acceptance criteria
- Videos continue to work without captions.
- Invalid extension, oversized files, invalid UTF-8, or files without a `WEBVTT` header are rejected.
- Valid `.vtt` files can be uploaded and replaced by authorized creators/editors using existing video permissions.
- A creator can remove an existing caption.
- The watch page exposes the caption track only when the viewer can already access the video.
- Shorts behavior remains unchanged.
- Existing upload/edit behavior, thumbnails, chapters, visibility, reactions, comments, analytics, and recommendations remain unchanged.

## Architecture
- Store the optional caption file on `Video`, following the existing video/thumbnail storage lifecycle.
- Keep WebVTT validation in a focused service/helper rather than the template.
- Reuse the existing upload/edit authorization and form flows.
- Use the browser's native `<track>` support; no JavaScript caption framework or external transcription service.

## Local validation
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test video.test_video_captions`
- `python manage.py test --parallel 4`
- `docker compose run --build --rm test`

## Out of scope
- Automatic speech-to-text transcription.
- Multiple languages or multiple caption tracks per video.
- Subtitle translation.
- Caption editing UI or cue-by-cue authoring.
- Burned-in captions.
- Shorts captions.
- External APIs, workers, AWS resources, or paid infrastructure.
