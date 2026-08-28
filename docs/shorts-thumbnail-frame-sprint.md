# Shorts Thumbnail Frame Sprint

## Goal
Let creators choose a frame from the source clip as the thumbnail for a generated Short.

## Scope
- Add optional thumbnail-frame seconds to the Short clip form.
- Require the selected frame to fall within the chosen source clip range.
- Generate a JPEG thumbnail locally with FFmpeg.
- Persist the selected source timestamp on `VideoShort`.
- Prepopulate the saved frame when re-rendering a derived Short.
- Replace the old generated thumbnail only after a successful re-render.
- Preserve the existing source-thumbnail fallback when no frame is selected.

## Acceptance criteria
1. Creators can set the thumbnail to the source player's current time.
2. Frame selection outside the chosen clip is rejected.
3. New derived Shorts use the generated frame when selected.
4. Re-rendering can change or clear the selected frame without changing the Short identity.
5. Failed thumbnail generation leaves an existing Short untouched.
6. Existing Shorts and creation flows continue working when no frame is selected.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_thumbnail_frame
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Architecture boundaries
- Local FFmpeg only.
- No external media service, AWS resource, paid API, queue, or Terraform change.
