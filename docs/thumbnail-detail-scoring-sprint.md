# Automatic Thumbnail Detail Scoring Sprint

## Goal
Improve automatic upload thumbnails so the existing bounded sampler prefers crisp, visually useful frames instead of relying only on brightness and contrast.

## Scope
- Keep the six candidate positions at 15%, 30%, 45%, 60%, 75%, and 90%.
- Add a lightweight edge-detail signal using Pillow's built-in `FIND_EDGES` filter.
- Preserve brightness, contrast, dark-frame, and overexposure safeguards.
- Add focused scoring regression coverage.

## Acceptance criteria
- Detailed candidates receive a modest scoring advantage over flat candidates.
- No OpenCV, NumPy, AI service, external API, or new package is required.
- Manual frame selection and custom thumbnails are unchanged.
- No schema, migration, cloud, AWS, paid-service, worker, queue, or Terraform changes.

## Verification
`python manage.py check`

`python manage.py makemigrations --check --dry-run`

`python manage.py test video.test_video_thumbnail_selection`

`python manage.py test --parallel 4`

`docker compose run --build --rm test`

## Out of scope
Face/object recognition, AI-generated thumbnails, additional FFmpeg samples, and thumbnail editing/cropping.
