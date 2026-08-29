# Shorts Thumbnail Format Preservation Sprint

## Goal

Keep stored thumbnail filenames aligned with the bytes they contain when Shorts reuse source thumbnails, while continuing to store FFmpeg-generated frame thumbnails as JPEG.

## Scope

- Preserve the source thumbnail suffix when no source-frame thumbnail is selected.
- Keep generated frame thumbnails as `.jpg` because the current FFmpeg thumbnail path produces JPEG output.
- Apply the same behavior to initial Short creation and source re-rendering.
- Add regression coverage for JPEG, PNG, and WebP fallback behavior and generated-frame JPEG behavior.

## Acceptance criteria

- A copied source PNG is saved with a `.png` suffix.
- A copied source WebP thumbnail remains `.webp` after re-rendering.
- Existing JPEG fallback behavior remains `.jpg`.
- A selected source-frame thumbnail remains `.jpg`.
- Thumbnail bytes are unchanged when copying an existing source thumbnail.
- No schema, migration, external service, or cloud change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_thumbnail_frame
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope

- Image transcoding or normalization.
- MIME sniffing or image-content validation.
- New thumbnail formats.
- Changes to upload validation.
- AWS, Terraform, paid services, workers, or queues.
