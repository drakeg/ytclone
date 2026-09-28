# Notification Cleanup Preview Sprint

## Goal
Show recipient-private eligible counts for each existing on-demand read-notification cleanup threshold so viewers can choose 7, 30, or 90 days with clear impact before submitting.

## Scope
- Count only the current recipient's read notifications older than each threshold, across the complete inbox rather than the current page/filter.
- Show those counts alongside each age option and explicitly explain their scope.
- Reuse the same eligibility query for the preview and POST deletion to avoid rule drift.
- Preserve the 30-day default and existing redirect/filter behavior.
- Add regression coverage for read-state, ownership, age thresholds, and displayed counts.

## Boundaries
No automatic deletion, API endpoint, schema, migration, dependency, background job, paid service, or infrastructure changes. This is a server-rendered snapshot; counts may change between page load and submission.

## Verification
```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_notification_pagination video.test_notifications
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```
