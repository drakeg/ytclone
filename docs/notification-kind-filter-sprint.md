# Notification Kind Filter Sprint

## Goal

Help signed-in viewers narrow a growing private notification inbox by activity type while composing cleanly with the existing All/Unread filter and pagination.

## Scope

- Add an optional notification-kind filter to the existing inbox.
- Support the notification kinds already defined by the model.
- Apply recipient ownership, unread state, and kind filtering before pagination.
- Preserve unread/kind filters through pagination and mark-read actions.
- Keep Mark all as read semantics unchanged: it marks the viewer's complete unread inbox, not only the filtered subset.
- Add focused regression coverage and keep Docker/non-Docker verification documented.

## Acceptance criteria

1. Notification inbox remains login-required and private to the current recipient.
2. A selected valid kind limits results to that kind before pagination.
3. Kind filtering composes with the existing unread filter.
4. Invalid kind values fall back safely to no kind filter.
5. Pagination links preserve active unread and kind filters.
6. Mark-read preserves active filter state and page.
7. Mark all as read continues to affect the current viewer's complete unread inbox.
8. Configuration, migration-drift, focused tests, and the full suite pass before readiness.

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

- Notification text search or date filters.
- Retention/deletion controls.
- Email, browser, push, or SMS delivery.
- Schema/migration/dependency changes.
- Workers, queues, AWS, paid services, or Terraform changes.
