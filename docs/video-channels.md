# Video Channel Ownership

## Sprint goal

Connect each new video to a creator-owned channel, backfill existing videos where ownership is unambiguous, and use that relationship for channel pages and subscriber upload notifications.

## Acceptance criteria

- Uploaders can select only channels they own and cannot submit another user's channel.
- Upload requires an owned channel; creators without one receive a clear validation message.
- Existing videos are assigned to their author's oldest channel when one exists and otherwise remain compatible with a nullable channel.
- Channel pages show only videos explicitly assigned to that channel.
- Subscribers receive one private notification for a new upload, while the uploader does not.
- Existing author ownership and authorization behavior remains intact.

## Architecture and migration

`Video.channel` will be a nullable foreign key for backward compatibility. A data migration will assign existing videos to each author's oldest channel. The upload form will scope its channel queryset to the authenticated user, and upload notifications will be created in the notification service with a bulk insert.

## Testing

Focused tests cover form scoping, forged channel submissions, no-channel behavior, channel-page isolation, migration-compatible null channels, and subscriber notifications. Run the full suite with `python manage.py check`, `python manage.py makemigrations --check --dry-run`, and `python manage.py test`, or `docker compose run --rm test`.

## Out of scope

- Moving videos between channels after upload
- Multiple channels per video
- Channel roles and team management
- Historical per-channel charts
- External notification delivery
