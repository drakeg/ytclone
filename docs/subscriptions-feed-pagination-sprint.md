# Subscriptions Feed Pagination Sprint

## Goal
Make the subscriptions feed useful beyond the newest 24 uploads by adding pagination and an optional followed-channel filter without changing subscription semantics.

## Scope
- Paginate visible long-form subscription uploads at 24 videos per page.
- Add an optional channel filter limited to channels the viewer actually follows and can access.
- Preserve the selected channel through pagination.
- Keep followed-channel cards visible above the feed.
- Keep Shorts in their dedicated experience.
- Preserve centralized video visibility and channel moderation rules.

## Acceptance criteria
- Page 1 shows at most 24 videos and older uploads are reachable on later pages.
- Videos remain newest-first with deterministic PK tie breaking.
- Selecting a followed channel shows only that channel's visible long-form uploads.
- An invalid or non-followed channel filter falls back to all followed channels.
- Pagination links preserve the selected channel filter.
- Draft, restricted, moderated, or otherwise invisible videos never appear.
- Empty states still distinguish no subscriptions from no available videos.

## Architecture
- Remove default hard slicing from the subscription service so it returns the complete visibility-safe queryset; retain the optional `limit` argument for compatibility.
- Normalize channel selection against the already-filtered followed-channel queryset.
- Keep Django `Paginator` in the view with a page size of 24.
- Reuse `_video_cards.html`; no schema or dependency changes.

## Validation
GitHub Actions run `34433521320` passed on the feature implementation:
- `python manage.py check` — passed.
- `python manage.py makemigrations --check --dry-run` — passed; no migration drift.
- `python manage.py test --parallel 4` — passed.

Focused subscription-feed regression coverage is included in `video/test_subscriptions_feed.py`, including pagination, channel filtering, invalid/non-followed filter fallback, visibility, ordering, and query-state preservation.

The repository Docker test command remains `docker compose run --build --rm test`; this sprint does not change Docker configuration.

## Out of scope
- Shorts inside the subscriptions feed.
- Notification changes.
- Recommendation ranking.
- Infinite scroll.
- Schema changes, new packages, workers, external services, AWS resources, or paid infrastructure.
