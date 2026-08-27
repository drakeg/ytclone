# Create Short from Long-Form Sprint

## Goal

Let a creator turn a selected segment of one of their existing standard videos into a new draft Short without leaving VideoShare.

## Design

The creator opens an owned/editable standard video, chooses a start and end time, title, and optional description, then VideoShare creates a new `Video` row plus `VideoShort` metadata pointing back to the source video and timestamps.

The derived Short is always created as a draft. It inherits the source channel and category, copies the source thumbnail and structured tags, and can then be reviewed/edited with the normal creator workflow before publication.

For this first implementation, media clipping is performed synchronously with FFmpeg. The Docker image installs FFmpeg so local/Docker testing is reproducible. The service copies source media into a temporary local file, invokes FFmpeg without a shell, then saves the generated MP4 through Django storage so the same service can work with local or remote media storage.

## Acceptance criteria

- Only authenticated users who can edit the source video can access the clip workflow.
- Existing Shorts cannot be used as long-form clip sources in this first version.
- Start/end values must be non-negative, end must be greater than start, and the selected segment is limited to 180 seconds.
- The generated Short is a new draft and never auto-publishes.
- The derived Short keeps source-channel/category context, copies the source thumbnail/tags, and records source video/start/end metadata.
- The source video is never modified.
- FFmpeg is invoked without `shell=True`, with bounded processing time and temporary-file cleanup.
- A failed media conversion does not leave a partially created Short row or orphaned generated output.
- The normal Short/video visibility, moderation, reporting, comments, analytics, and monetization rules continue to apply to the derived Short.
- Docker includes FFmpeg; no external transcoding provider, worker, queue, AWS resource, or paid service is added.

## Out of scope

- Automatic vertical crop/reframing
- Browser timeline/scrubber editing
- AI clip suggestions
- Transcript-based clipping
- Background/async rendering
- Multiple clips in one request
- Music overlays, captions, stickers, or effects
- Terraform changes

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_from_long_form
python manage.py test --parallel 4
docker compose run --build --rm test
```
