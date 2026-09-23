# Notification Date Filter Sprint

## Goal

Help signed-in viewers narrow a busy private notification inbox by recency while preserving existing read-state, activity-type, privacy, and pagination behavior.

## Scope

- Add a bounded notification date filter.
- Support any time, today, past 7 days, and past 30 days.
- Compose date filtering with existing All/Unread and activity-type filters before pagination.
- Preserve filter, activity type, date range, and page when marking one notification read.
- Preserve active filters through pagination and filter controls.
- Keep Mark all as read scoped to the full current viewer inbox.
- Add focused regression coverage and current verification instructions.

## Acceptance criteria

1. Notification inbox remains login-required and current-viewer-only.
2. Default date filter is any time.
3. Valid date ranges filter by notification creation time before pagination.
4. Invalid date values safely fall back to any time.
5. Date, read-state, and activity-type filters compose.
6. Pagination preserves active filters.
7. Mark read preserves active filters and page.
8. Mark all as read still affects the full current viewer unread inbox regardless of active filters.
9. Configuration, migration-drift, focused tests, and full suite pass before readiness.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_notification_pagination
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Notification retention/deletion.
- Full-text notification search.
- Email, push, SMS, or browser notifications.
- Schema/migration/dependency changes.
- External services, workers, AWS, paid services, or Terraform changes.
