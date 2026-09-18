# Notification inbox filters sprint

## Goal

Make a busy private notification inbox easier to triage by letting viewers switch between all notifications and unread notifications while preserving the existing pagination and read actions.

## Scope

- Add an `All` / `Unread` filter to the authenticated notification inbox.
- Apply the selected filter before pagination.
- Preserve the selected filter through Previous/Next links.
- Preserve the selected filter and current page when marking one notification read.
- Keep `Mark all as read` scoped to the viewer's full inbox, matching current behavior.
- Keep recipient privacy, newest-first ordering, and 24-item page size unchanged.
- Add focused regression coverage for filtering, pagination state, invalid filter fallback, privacy, and read redirects.

## Acceptance criteria

1. `/videos/notifications/?filter=unread` shows only the signed-in viewer's unread notifications.
2. Missing or unsupported filter values safely fall back to `all`.
3. Filtering occurs before pagination, so read notifications do not consume unread-page slots.
4. Pagination links retain the active filter.
5. Marking one notification read returns to the same page/filter when those values were submitted.
6. Mark all as read continues to mark every unread notification belonging to the viewer, not only the current filtered page.
7. Another user's notifications never appear or become mutable.
8. Django checks, migration drift checks, and the full test suite pass.

## Exclusions

- Notification search or date filters.
- Notification-kind/category filters.
- Retention or deletion controls.
- Email, push, SMS, or browser delivery changes.
- Schema changes or new dependencies.
- External services, workers, AWS, or paid infrastructure.

## Architecture

Extend the existing focused `notification_views.py` module. Normalize the query-string filter to a small allowlist, filter the current user's notification queryset before passing it to `Paginator`, and pass the normalized filter to the template. Read redirects use Django URL reversing plus encoded query parameters rather than trusting arbitrary redirect targets.

The template uses ordinary links/forms so the feature remains server-rendered and works without JavaScript.

## Validation

CI must run Django configuration checks, migration drift checks, and the complete test suite. The PR remains draft until those checks are green.

Local verification, with and without Docker:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_notification_pagination
python manage.py test --parallel 4
docker compose run --build --rm test
```
