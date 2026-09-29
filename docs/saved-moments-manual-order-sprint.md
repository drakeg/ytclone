# Saved Moments Manual Order Sprint

## Goal
Let viewers maintain a private manual order for Saved moments while preserving newest, oldest, video-title, and playback-timestamp sorting.

## Data design
- Add `VideoBookmark.sort_position` as a non-negative integer.
- Backfill each user's existing bookmarks into deterministic newest-saved-first manual order.
- New bookmarks append to the end of that user's manual order.
- Manual reordering updates positions transactionally.
- Reordering operates among bookmarks whose videos remain visible to the viewer; inaccessible bookmark records are retained and never exposed.

## Scope
- Add a Manual order sort option.
- Add POST-only Move up / Move down controls only when Manual order is selected.
- Preserve active search, Manual order, and page state after moving.
- Reject forged, other-user, inaccessible, or invalid-direction moves.
- Keep all existing bookmark search, playback seeking, deletion, bulk cleanup, and other sorts unchanged.
- Update migration-leaf regression coverage and administrator visibility for the new field.

## Acceptance criteria
1. Existing bookmarks receive stable per-user manual positions in newest-first order.
2. New bookmarks append without disturbing prior manual order.
3. Manual moves are current-user scoped and POST-only.
4. Inaccessible bookmarks are preserved but do not block moving between adjacent visible bookmarks.
5. Boundary moves are safe no-ops.
6. Search filters display results without redefining the full visible manual queue.
7. Existing sorts and privacy behavior remain unchanged.
8. Migration drift and full tests pass locally/CI/Compose.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_bookmarks video.test_migrations
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope
Drag-and-drop UI, cross-account sharing, automatic reordering, external services, paid infrastructure, and changes to video playback timestamps.
