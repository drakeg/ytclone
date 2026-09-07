# Automatic Thumbnail Detail Scoring Sprint

## Goal

Improve automatic upload thumbnails so the existing six-frame sampler prefers visually useful, crisp frames rather than relying only on brightness and contrast.

## Scope

- Keep the bounded six-frame sampling strategy and existing upload workflow.
- Add a lightweight edge-detail signal using Pillow's built-in `FIND_EDGES` filter.
- Give detailed frames a modest score bonus and strongly flat frames a small penalty.
- Preserve brightness, contrast, dark-frame, and overexposure safeguards.
- Add focused scoring regression coverage.

## Acceptance criteria

- Automatic thumbnail generation still samples only 15%, 30%, 45%, 60%, 75%, and 90% of the video.
- A crisp, detailed candidate outranks an otherwise flat mid-brightness candidate.
- No OpenCV, NumPy, AI service, external API, or new package is required.
- Manual frame selection and custom thumbnail uploads are unchanged.
- No schema, migration, cloud, AWS, paid-service, worker, queue, or Terraform changes.

## Verification

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_thumbnail_selection
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope

- Face detection or object recognition.
- AI-generated thumbnails.
- Changing the number of FFmpeg sample frames.
- Editing or cropping a selected thumbnail.
