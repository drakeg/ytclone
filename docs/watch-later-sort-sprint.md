# Watch Later Sort Sprint

## Goal

Give signed-in viewers simple ordering controls for their private Watch Later queue while preserving search, visibility, and pagination behavior.

## Scope

- Add bounded sorting to Watch Later.
- Support newest saved, oldest saved, and video title.
- Compose sorting with existing title search before pagination.
- Preserve query, sort, and page state when removing a video.
- Keep the current 24-item pagination and video visibility rules.
- Add focused regression coverage and current verification instructions.

## Acceptance criteria

1. Watch Later remains login-required and private to the current viewer.
2. Default ordering remains newest saved first.
3. Valid sort options reorder only visible videos already in the viewer's Watch Later queue.
4. Invalid sort values safely fall back to newest.
5. Search and sort compose before pagination.
6. Pagination preserves active query and sort.
7. Removal preserves active query, sort, and page.
8. Configuration, migration-drift, focused tests, and full suite pass before readiness.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_watch_later
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Manual/drag-and-drop queue ordering.
- Playlist schema changes.
- Saved moments/history behavior.
- External services, workers, AWS, paid services, dependencies, or Terraform changes.
