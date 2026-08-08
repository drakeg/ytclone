# Video Channel Ownership

## Delivered behavior

Each new video now belongs to a creator-owned channel. Existing videos are backfilled where ownership is unambiguous, channel pages use the explicit relationship, and subscribers receive new-upload notifications.

## Delivered safeguards

- Uploaders can select only channels they own and cannot submit another user's channel.
- Upload requires an owned channel; creators without one receive a clear validation message.
- Existing videos are assigned to their author's oldest channel when one exists and otherwise remain compatible with a nullable channel.
- Channel pages show only videos explicitly assigned to that channel.
- Subscribers receive one private notification for a new upload, while the uploader does not.
- Existing author ownership and authorization behavior remains intact.

## Architecture and migration

`Video.channel` is a nullable foreign key for backward compatibility. Migration `0007_video_channel` assigns existing videos to each author's oldest channel when available. The upload form scopes its channel queryset to the authenticated user, and the notification service creates subscriber upload notifications with a bulk insert.

## Testing

Focused tests cover form scoping, forged channel submissions, no-channel behavior, channel-page isolation, migration-compatible null channels, and subscriber notifications. The sprint-close non-Docker run passed Django checks, reported no migration drift, and completed all 86 tests successfully. Docker remains unavailable on the delivery host; use `docker compose run --rm test` on a Docker-enabled machine.

No dependencies, environment variables, AWS resources, or external services are added.

## Out of scope

- Moving videos between channels after upload
- Multiple channels per video
- Channel roles and team management
- Historical per-channel charts
- External notification delivery
