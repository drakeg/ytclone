# Notification Pagination Sprint

## Goal
Keep the private notifications inbox usable as activity grows by paging notifications instead of rendering the entire history at once.

## Scope
- Paginate the authenticated viewer's notifications at 24 per page.
- Preserve existing newest-first notification ordering.
- Keep unread/read styling and per-notification Mark read actions unchanged.
- Preserve the existing Mark all as read behavior across the viewer's complete notification inbox, not only the current page.
- Preserve the current page when marking an individual notification as read.
- Keep notification privacy strictly scoped to the authenticated recipient.

## Acceptance criteria
- The notifications page renders at most 24 notifications per page.
- Older notifications are reachable through Previous/Next navigation.
- Invalid or out-of-range page values fall back safely through Django paginator behavior.
- Marking one notification as read only changes that notification and returns the viewer to the same page when possible.
- Mark all as read continues to update every unread notification for the current viewer.
- Other users' notifications never appear or become mutable.
- Empty inbox behavior remains intact.

## Architecture
- Use Django `Paginator` in `notification_list` with a page size of 24.
- Paginate the existing recipient-scoped queryset after `select_related` optimization.
- Pass the current page through the single-notification Mark read form so its redirect can preserve context.
- Notification request dispatch is moved to a focused view module while preserving the existing named URL reversals.
- No schema or dependency changes.

## Out of scope
- Notification type filters.
- Search.
- Infinite scroll.
- Notification retention policies.
- Email, push, SMS, or browser delivery changes.
- New packages, workers, external services, AWS resources, or paid infrastructure.

## Validation
GitHub Actions run `34796542692` on the implementation head passed:
- `python manage.py check` — passed; no issues.
- `python manage.py makemigrations --check --dry-run` — passed; no changes detected.
- `python manage.py test --parallel 4` — passed; 658 tests run, 1 skipped.

The final documentation-only commit must also pass the same CI workflow before the PR is marked ready for review.

Local container verification uses `docker compose run --build --rm test` after
the listed non-Docker commands.
