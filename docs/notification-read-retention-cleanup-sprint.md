# Notification Read-Retention Cleanup Sprint

## Goal

Let viewers intentionally clean old **read** notifications from their private inbox without introducing automatic deletion, scheduled jobs, or a schema change.

## Scope

- Add a POST-only cleanup action for the signed-in recipient.
- Let the viewer choose a bounded age threshold: 7, 30, or 90 days.
- Delete only notifications that are both read and older than the selected threshold.
- Keep unread notifications regardless of age.
- Keep other users' notifications untouched.
- Preserve active inbox read/type/date/search/page state after cleanup.
- Show the cleanup control on the notification inbox with a conservative 30-day default.
- Add focused regression coverage for age boundaries, read-state protection, ownership, invalid thresholds, POST-only behavior, and state preservation.

## Acceptance criteria

1. A viewer can delete read notifications older than 7, 30, or 90 days.
2. Unread notifications are never deleted by retention cleanup.
3. Another recipient's notifications are never affected.
4. Invalid thresholds safely fall back to 30 days.
5. Notifications exactly at or newer than the cutoff are retained.
6. The action rejects GET.
7. Existing search/filter, Mark read, Mark all read, and selected deletion behavior remains unchanged.
8. No schema, migration, dependency, background worker, queue, external service, AWS, or paid-service changes.
9. Focused and full CI pass before readiness.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_notification_pagination video.test_notifications
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Automatic scheduled retention.
- Deleting unread notifications through retention cleanup.
- Per-notification-type retention policies.
- Email, push, SMS, or external notification delivery.
