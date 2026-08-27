# Automatic Shorts Detection Sprint

## Goal

Remove unnecessary creator guesswork during upload by inspecting the uploaded media and automatically classifying clear short-form vertical/square videos as Shorts while preserving an explicit creator override.

## Classification rule

For new uploads using **Auto-detect**:

- Short: the primary video stream is portrait or square (`height >= width`) **and** duration is 180 seconds or less.
- Standard video: landscape media, media longer than 180 seconds, or media whose dimensions/duration cannot be determined reliably.

The rule is intentionally deterministic and conservative. A short horizontal clip is not automatically made a Short, and a long vertical recording remains a standard video. Creators can explicitly select Standard video or Short to override the automatic result.

## Design

- Use local `ffprobe`, shipped with the existing FFmpeg Docker dependency, to read primary video-stream dimensions, rotation metadata, and duration.
- Correct width/height interpretation for 90/270-degree rotation metadata before deciding orientation.
- Probe the upload before persistence and rewind the uploaded file afterward so normal Django file saving is unaffected.
- Failure to probe does not block a valid upload; Auto-detect falls back to Standard video.
- Existing videos retain their current format during edit unless the creator explicitly selects a different format.
- No new schema is required; `VideoShort` remains the source of truth for Short classification.

## Acceptance criteria

- Auto-detect is the default for new uploads.
- Portrait/square videos up to 180 seconds create `VideoShort` metadata automatically.
- Landscape videos remain standard videos even when short.
- Portrait/square videos over 180 seconds remain standard videos.
- Rotation metadata is respected.
- Explicit Standard video and Short selections override detection.
- Probe failures fall back safely without blocking upload.
- Existing video edits do not silently reclassify media.
- Uploaded file pointers are restored after probing.
- No external service, cloud transcoder, worker, queue, AWS resource, paid service, or Terraform change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_auto_detection
python manage.py test --parallel 4
docker compose run --build --rm test
```
