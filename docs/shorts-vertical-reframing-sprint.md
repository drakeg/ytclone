# Shorts Vertical Reframing Sprint

## Goal

Let creators intentionally turn a long-form clip into a vertical 9:16 Short without requiring external editing software, while preserving the existing original-frame option.

## Scope

- Add creator-selectable framing modes when deriving a Short:
  - Keep original frame
  - Vertical 9:16 — focus left
  - Vertical 9:16 — focus center
  - Vertical 9:16 — focus right
- Show an in-browser 9:16 framing preview tied to the chosen focus.
- Render vertical modes locally with FFmpeg at 720x1280 using scale-to-fill plus crop.
- Store the selected framing mode on `VideoShort` metadata for provenance and future editor/rerender work.
- Keep generated Shorts as drafts and retain the existing 180-second limit, source linkage, rollback behavior, and normal publication/moderation rules.

## Acceptance criteria

- Original-frame mode preserves the existing clipping behavior.
- Vertical modes produce a 720x1280 H.264/AAC MP4 and use deterministic left/center/right horizontal crop focus.
- Browser preview communicates the selected vertical crop before generation.
- Invalid framing values are rejected server-side.
- The selected framing mode is persisted on the derived Short metadata.
- Conversion failures leave no partial database rows or generated files.
- Existing long-form source media is never modified.

## Out of scope

- Face/object tracking
- AI auto-reframing
- Arbitrary drag-to-pan crop coordinates
- Zoom/keyframes
- Captions/effects/music
- Async rendering, workers, queues, cloud transcoding, AWS/Terraform changes

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_vertical_reframing
python manage.py test --parallel 4
docker compose run --build --rm test
```
