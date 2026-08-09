# Per-Channel Analytics

## Sprint goal

Give channel owners a private analytics view scoped to one explicitly owned channel.

## Acceptance criteria

- Only the channel owner can access its analytics; other authenticated users receive 404 and anonymous users are redirected.
- Totals include only videos assigned to that channel.
- Metrics include uploads, views, likes, dislikes, and subscribers.
- A deterministic performance table ranks channel videos by views and likes.
- Legacy videos without a channel are excluded.
- Aggregation remains in the analytics service and requires no stored rollups.

## Architecture and testing

The existing analytics service will add a channel-scoped snapshot. The view resolves the channel using both its ID and `request.user`, preventing user-selectable cross-owner access. Focused tests cover authentication, authorization, isolation, totals, ordering, empty states, and owner links.

Run `python manage.py check`, `python manage.py makemigrations --check --dry-run`, and `python manage.py test`, or run `docker compose run --rm test`.

## Out of scope

- Historical trends and date ranges
- Watch time and retention
- CSV exports
- Channel teams and delegated access
- Background aggregation or third-party analytics
