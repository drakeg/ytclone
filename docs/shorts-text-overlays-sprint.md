# Shorts Text Overlay Sprint

## Goal
Let creators add one optional text callout to Shorts generated from long-form source videos, with simple placement controls and live preview guidance.

## Scope
- Add optional overlay text to the existing Short clip form.
- Support top, center, and bottom placement.
- Burn the overlay into generated media with the existing local FFmpeg pipeline.
- Persist overlay text/placement on `VideoShort` so re-rendering retains the creator's choice.
- Allow the existing derived-Short re-render editor to change or remove the overlay.
- Install DejaVu Sans in the application container for deterministic FFmpeg text rendering.
- Keep the overlay optional; blank text means no text filter.

## Acceptance criteria
1. A creator can create a derived Short with or without overlay text.
2. Overlay text is limited to 120 characters.
3. Overlay placement is restricted to top, center, or bottom.
4. FFmpeg receives a drawtext filter only when overlay text is non-empty.
5. Re-rendering prepopulates and updates saved overlay settings.
6. Existing Shorts without overlays continue to render exactly as before.
7. Failed rendering leaves existing Short media and overlay metadata unchanged.

## Tests
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_text_overlays
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Architecture boundaries
- Local FFmpeg only.
- No AI caption generation, speech-to-text, worker, queue, cloud transcoding, AWS resource, external API, or paid service.
- No multi-layer graphics timeline in this sprint.
