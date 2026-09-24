# Notification Inbox Routing and Bulk Cleanup Sprint

## Goal

Make the modular notification inbox implementation the canonical routed code path, then add private bulk deletion without duplicating notification behavior.

## Scope

- Route notification list/read actions through `video.notification_views`.
- Remove the legacy duplicate notification handlers from `video.views`.
- Add checkbox selection to the private notification inbox.
- Add a POST-only bulk-delete endpoint scoped to the signed-in recipient.
- Ignore malformed, duplicate, forged, and other-user notification IDs.
- Preserve active search, read-state, activity-type, date, and page state after bulk deletion.
- Keep Mark read and Mark all as read behavior unchanged.
- Add regression coverage proving the routed inbox uses search/filter/pagination behavior and bulk deletion remains recipient-scoped.

## Acceptance criteria

1. `notification_list`, `notification_mark_read`, and `notification_mark_all_read` routes resolve to `video.notification_views`.
2. Existing notification search, read-state, kind, date, and pagination behavior is active through the public URLs.
3. A viewer can remove multiple selected notifications belonging to that viewer.
4. Forged IDs belonging to another recipient are not deleted.
5. Empty, malformed, and duplicate selections are safe.
6. Search/filter/date/page state is preserved after deletion.
7. Bulk deletion rejects GET.
8. No schema, migration, dependency, external-service, AWS, paid-service, worker, queue, or Terraform changes.
9. Focused and full CI pass before readiness.

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

- Automatic notification retention/expiry.
- Email, SMS, push, or browser delivery.
- New notification event types.
- Schema changes.
