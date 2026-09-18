# Watch History Pagination Sprint

## Goal
Keep large private watch histories usable by paging visible history entries instead of rendering the full history at once.

## Scope
- Paginate the signed-in viewer's visible watch-history entries at 24 per page.
- Preserve most-recently-watched-first ordering across pages.
- Continue filtering inaccessible videos through centralized visibility rules before pagination.
- Keep existing remove-entry and clear-history behavior unchanged.
- Preserve the existing private-history access boundary and empty state.

## Acceptance criteria
- The History page renders at most 24 visible entries per page.
- Older history entries are reachable through Previous/Next navigation.
- Invalid or out-of-range page values fall back safely through Django paginator behavior.
- Hidden, moderated, deleted, or otherwise inaccessible videos do not appear or consume visible page slots.
- Removing a displayed history entry affects only the current viewer's history.
- Clearing history removes the viewer's entire history regardless of the current page.

## Architecture
- Use Django `Paginator` in `watch_history` with a page size of 24.
- Paginate the existing viewer-scoped, visibility-filtered history queryset.
- Reuse the existing history template and mutation endpoints.
- No schema or dependency changes.

## Out of scope
- History search or filtering.
- Date grouping.
- Infinite scroll.
- Retention/automatic deletion rules.
- Recommendation changes.
- New packages, workers, external services, AWS resources, or paid infrastructure.

## Validation
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- focused watch-history pagination tests
- full test suite
- `docker compose run --build --rm test`
