# Notification Search Sprint

## Goal

Add private keyword search to the signed-in viewer's notification inbox while preserving the existing read-state, activity-type, date, pagination, and mutation behavior.

## Scope

- Add an optional `q` search parameter to the private notification inbox.
- Match case-insensitively against notification actor username/name, video title, and channel name.
- Apply search before pagination and compose it with existing unread, activity-type, and date filters.
- Preserve the active search query through read-filter links, filter form submission, pagination, and per-notification Mark read actions.
- Keep Mark all as read scoped to every unread notification for the current viewer, matching current behavior.
- Add query-aware empty-state text and focused regression coverage.

## Acceptance criteria

1. A viewer can search only their own notifications.
2. Search matches actor identity, video title, and channel name case-insensitively.
3. Search composes with unread, activity-type, and date filters before pagination.
4. Pagination and per-notification Mark read preserve the active query.
5. Empty search results are distinguished from an inbox with no notifications.
6. Unsupported or blank search input does not alter existing behavior.
7. No schema, migration, dependency, external-service, AWS, paid-service, worker, queue, or Terraform changes.
8. Focused and full CI pass before readiness.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_notifications video.test_notification_pagination
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Notification retention/deletion controls.
- Fuzzy matching, typo correction, ranking, or external search services.
- Searching notification body text stored in a new column.
- Email, push, SMS, browser notifications, or digest delivery.
