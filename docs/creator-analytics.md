# Creator Analytics

## Delivered behavior

Authenticated creators now have a private dashboard summarizing the upload, view, reaction, and subscriber data already stored by the application.

## Metrics and privacy

- The dashboard is available only to authenticated users and always scopes data to the current user.
- Summary cards show total uploads, views, likes, dislikes, and unique subscribers.
- A video performance table shows the creator's videos ordered by views, with reaction counts and publication dates.
- Creators with no videos or channels receive useful zero and empty states.

## Delivered safeguards

- Anonymous users are redirected to login.
- No URL parameter can be used to request another creator's analytics.
- Summary totals exclude every other user's videos and channels.
- A subscriber following more than one channel owned by the creator is counted once.
- Video rows include views, likes, dislikes, and publication date and are ordered deterministically.
- Aggregation logic lives in a service module rather than the view.
- The dashboard requires no new tracking, cookies, external services, or paid infrastructure.

## Architecture

Analytics query construction lives in `video/services/analytics.py`. The login-protected view passes only `request.user` to the service and renders the returned snapshot. The dashboard calculates current lifetime totals from existing relational data; it does not introduce stored rollups or event tables.

This first version is creator-level rather than channel-level because videos currently belong directly to users, while channels are separate records owned by a user. Unique subscribers will be aggregated across all channels owned by that creator.

## Test plan

`video/test_creator_analytics.py` covers authentication, creator isolation, empty states, unique subscriber aggregation, totals, deterministic video ordering, rendered output, and navigation.

The sprint-close non-Docker run completed successfully with 70 tests. Django system checks passed, the migration-drift check reported no changes, the Docker test script passed syntax validation, and Python modules passed bytecode compilation. Docker execution was unavailable in the delivery environment because Docker was not installed; the documented Compose test command remains unchanged.

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

## Migration and configuration

The original analytics sprint added no migration. Watch-time analytics adds
migration `0020_video_watch_events` but no dependency, environment variable, AWS
resource, cookie category, or external service.

## Out of scope

- Historical trends, date-range comparisons, and charts
- Traffic sources and geography
- Per-channel video analytics until videos have an explicit channel relationship
- CSV export or scheduled reports
- Background aggregation, data warehouses, or third-party analytics services

## Delivered: Watch-time analytics

Bounded, idempotent playback heartbeats feed private aggregate creator metrics.
The initial retention view uses quarter marks (25/50/75/100%, with 95% treated
as completed) rather than a second-by-second curve.

The creator-facing metrics are:

- Total watch time, displayed in minutes or hours, for each video and channel
- Average view duration per qualifying playback
- Average percentage viewed, based on the video's duration
- A per-video retention view that shows where viewers stop watching
- Lifetime and bounded date-range summaries

The playback-progress field exists to resume an authenticated viewer's
video. It stores the latest position, not elapsed viewing activity, so summing it
would produce inaccurate watch hours. Dedicated incremental telemetry supports
authenticated and anonymous sessions; anonymous identifiers are one-way hashes.

The sprint must define and test safeguards for repeated events, seeking,
background tabs, simultaneous sessions, completion, malformed durations, and
privacy isolation. Raw viewer-level activity must remain private; creators should
receive only aggregate metrics for videos and channels they own. Local testing
must cover both Docker and non-Docker workflows before sprint closure.

Migration `0020_video_watch_events` stores capped heartbeat events. Collection
and aggregation live in `video/services/watch_time.py`. Django checks,
migration-drift checks, and all 295 tests passed both directly and through Docker
Compose.
