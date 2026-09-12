# Watch Later Pagination Sprint

## Goal
Keep large Watch Later queues easy to browse by paging saved videos instead of rendering the entire private queue at once.

## Scope
- Paginate the authenticated viewer's visible Watch Later videos at 24 per page.
- Preserve newest-saved-first ordering across pages.
- Keep existing add/remove behavior and the reserved private Watch Later playlist semantics unchanged.
- Continue filtering inaccessible videos through centralized video visibility rules before pagination.
- Keep the existing Watch Later empty state and navigation entry.

## Acceptance criteria
- The Watch Later page renders at most 24 visible videos per page.
- Additional saved videos are reachable through Previous/Next navigation.
- Invalid or out-of-range page values fall back safely through Django paginator behavior.
- Hidden, restricted, moderated, deleted, or otherwise inaccessible videos do not appear or consume visible page slots.
- Removing a video from a displayed page continues to affect only the current viewer's private Watch Later queue.
- Saved moments remain unrelated timestamp bookmarks.

## Architecture
- Use Django `Paginator` in `watch_later_views.watch_later` with a page size of 24.
- Paginate the existing visibility-safe queryset returned by `watch_later_videos`.
- Reuse `_video_cards.html` and existing Watch Later add/remove endpoints.
- No schema or dependency changes.

## Out of scope
- Reordering controls.
- Search or filtering inside Watch Later.
- Automatic removal after playback completion.
- Infinite scroll.
- Shorts-specific behavior.
- New packages, workers, external services, AWS resources, or paid infrastructure.

## Delivered
- Watch Later now pages its visibility-safe queue at 24 videos per page.
- Newest-saved-first ordering is preserved across page boundaries.
- Previous/Next controls are shown only when more than one page exists.
- The existing Watch Later action preserves the current query string, so removing a video from a later page returns the viewer to that page when it remains valid.
- Focused regression coverage verifies page size, ordering, visibility-before-pagination, and invalid page fallback.

## Validation
GitHub Actions run `34674133903` passed on the implementation head:
- `python manage.py check` — passed.
- `python manage.py makemigrations --check --dry-run` — passed; no migration drift.
- `python manage.py test --parallel 4` — passed.

The repository Docker test command remains `docker compose run --build --rm test`; this sprint does not change Docker configuration.
