# In-App Notifications

## Delivered behavior

Creators now receive private, database-backed notifications for new comments, reactions, and subscriptions without external delivery infrastructure.

## Events and unread state

- Creators receive notifications when another user comments on or reacts to their video.
- Channel owners receive notifications when another user subscribes.
- Users never receive notifications for their own activity or for removals and unsubscribe actions.
- An authenticated inbox shows newest notifications first with unread state.
- Users can mark one notification or all notifications as read.
- The navigation displays the current user's unread count.

## Delivered safeguards

- Every query and mutation is scoped to `request.user`.
- Anonymous users are redirected to login.
- Cross-user read mutations return 404 without changing data.
- Notification mutations accept POST only and retain CSRF protection.
- Notification creation is isolated in a service module.
- The feature introduces no email, push, background workers, polling, or paid services.

## Architecture

`Notification` stores recipient, optional actor, event kind, optional video or channel target, creation time, and read time. `video/services/notifications.py` creates event records and keeps self-notification rules out of views. A context processor provides only the authenticated user's unread count to navigation.

## Test plan

`video/test_notifications.py` covers event creation, self-event suppression, unsubscribe/removal behavior, inbox privacy, unread counts, POST-only mutations, cross-user protection, mark-all behavior, and empty states.

The sprint-close non-Docker run completed successfully with 80 tests. Django system checks passed, the migration-drift check reported no changes, the Docker test script passed syntax validation, and Python modules passed bytecode compilation. Docker execution remained unavailable because Docker is not installed on the delivery host.

Without Docker:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

With Docker:

```bash
docker compose run --rm test
```

Terraform checks are not applicable unless Terraform files or workflows change.

## Migration and configuration

Migration `0006_notification` creates the notification table and its user, video, and channel relationships. No dependencies, environment variables, AWS resources, background workers, or external services are added.

## Out of scope

- Email, browser push, SMS, and mobile push
- Real-time sockets and polling
- Notifications for new uploads until videos explicitly belong to channels
- User notification preferences and digest schedules
- Background workers and external message brokers
