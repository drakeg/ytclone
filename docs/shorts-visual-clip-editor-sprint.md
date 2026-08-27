# Visual Shorts Clip Editor Sprint

## Goal

Make creating a Short from a long-form video fast and intuitive by replacing manual timestamp entry as the primary workflow with an interactive video-backed clip selector.

## Scope

- Keep the existing server-validated `start_seconds` / `end_seconds` fields and FFmpeg pipeline as the source of truth.
- Add start/end range controls synchronized with the source video's metadata duration.
- Add **Set start to current time** and **Set end to current time** controls beside the preview player.
- Show the selected start, end, and clip duration in human-readable time.
- Keep the selected range capped at 180 seconds in the browser while retaining all existing server-side validation.
- Let creators preview the selected clip by jumping to its start and stopping playback at the selected end.
- Degrade gracefully: if JavaScript or media metadata is unavailable, the ordinary numeric start/end fields remain usable.
- Add focused regression tests for the visual-editor markup and preservation of the existing form/backend contract.

## Acceptance criteria

- Existing long-form-to-Short creation continues working without JavaScript.
- The source duration configures the visual start/end ranges when media metadata loads.
- Moving either range updates the existing form fields and selected-duration summary.
- Selecting a range longer than 180 seconds is automatically constrained client-side and remains rejected server-side if bypassed.
- Current player time can populate either boundary.
- Preview starts at the selected start and stops at the selected end.
- No schema, migration, transcoding, storage, infrastructure, or FFmpeg behavior changes are required.

## Out of scope

- Thumbnail waveform generation
- Frame-by-frame thumbnail strips
- Vertical crop/reframing
- Captions, text overlays, music, effects, or filters
- AI clip suggestions
- Async rendering/workers
- AWS/Terraform changes

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_visual_editor
python manage.py test --parallel 4
docker compose run --build --rm test
```
