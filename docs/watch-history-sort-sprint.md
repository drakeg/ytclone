# Watch History Sort Sprint

## Goal

Give signed-in viewers useful ordering controls for their private Watch History while preserving search, visibility, pagination, and clear-history behavior.

## Scope

- Add bounded sorting to Watch History.
- Support recently watched, oldest watched, and video title.
- Compose sorting with existing title search before pagination.
- Preserve query, sort, and page state when removing an entry.
- Keep the existing 24-item pagination and visibility filtering.
- Keep Clear history as a full current-viewer action.
- Add focused regression coverage and current verification instructions.

## Acceptance criteria

1. Watch History remains login-required and current-user-only.
2. Default ordering remains recently watched first.
3. Valid sort options reorder only visible current-viewer history entries.
4. Invalid sort values safely fall back to recent.
5. Search and sort compose before pagination.
6. Pagination preserves active query and sort.
7. Removal preserves active query, sort, and page.
8. Clear history still clears the full current viewer history, regardless of filters.
9. Configuration, migration-drift, focused tests, and full suite pass before readiness.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_watch_history
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- History schema/retention changes.
- Bulk selection.
- Watch Later/Saved moments behavior.
- External services, workers, AWS, paid services, dependencies, or Terraform changes.
