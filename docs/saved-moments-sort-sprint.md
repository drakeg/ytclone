# Saved Moments Sort Sprint

## Goal

Give signed-in viewers useful ordering controls for their private Saved moments list without changing bookmark privacy, search, or playback behavior.

## Scope

- Add a bounded sort option to Saved moments.
- Support newest saved, oldest saved, video title, and playback timestamp.
- Compose sorting with the existing private search before pagination.
- Preserve search and sort through pagination and list removal.
- Keep existing visibility filtering and 24-item pagination.
- Add focused regression coverage and current verification instructions.

## Acceptance criteria

1. Saved moments remain login-required, current-user-only, and visibility-safe.
2. Default ordering remains newest saved first.
3. Valid sort options reorder only the already-visible current viewer bookmarks.
4. Invalid sort values safely fall back to newest.
5. Search and sort compose before pagination.
6. Pagination links preserve active search and sort state.
7. Remove-from-list preserves search, sort, and page state.
8. Configuration, migration-drift, focused tests, and full suite pass before readiness.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_bookmarks
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Bookmark schema or label editing.
- Drag/drop or manual ordering.
- Bulk deletion.
- Watch Later/history behavior.
- External services, workers, AWS, paid services, dependencies, or Terraform changes.
