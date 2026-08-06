# Creator Analytics

## Sprint goal

Give authenticated creators a private dashboard summarizing the upload, view, reaction, and subscriber data already stored by the application.

## Planned behavior

- The dashboard is available only to authenticated users and always scopes data to the current user.
- Summary cards show total uploads, views, likes, dislikes, and unique subscribers.
- A video performance table shows the creator's videos ordered by views, with reaction counts and publication dates.
- Creators with no videos or channels receive useful zero and empty states.

## Acceptance criteria

- Anonymous users are redirected to login.
- No URL parameter can be used to request another creator's analytics.
- Summary totals exclude every other user's videos and channels.
- A subscriber following more than one channel owned by the creator is counted once.
- Video rows include views, likes, dislikes, and publication date and are ordered deterministically.
- Aggregation logic lives in a service module rather than the view.
- The dashboard requires no new tracking, cookies, external services, or paid infrastructure.

## Architecture

Analytics query construction will live in `video/services/analytics.py`. A login-protected view will pass only `request.user` to the service and render the returned snapshot. The dashboard will calculate current lifetime totals from existing relational data; it will not introduce stored rollups or event tables.

This first version is creator-level rather than channel-level because videos currently belong directly to users, while channels are separate records owned by a user. Unique subscribers will be aggregated across all channels owned by that creator.

## Test plan

Focused tests will cover authentication, creator isolation, empty states, unique subscriber aggregation, totals, deterministic video ordering, and rendered output.

Run the full suite without Docker:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Run the same suite in Docker:

```bash
docker compose run --rm test
```

Terraform checks are not applicable unless files under `terraform/` or its workflow change.

## Out of scope

- Historical trends, date-range comparisons, and charts
- Watch time, retention, traffic sources, and geography
- Per-channel video analytics until videos have an explicit channel relationship
- CSV export or scheduled reports
- Background aggregation, data warehouses, or third-party analytics services
