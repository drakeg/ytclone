# In-App Notifications

## Sprint goal

Add private, database-backed notifications so creators can see new comments, reactions, and subscriptions without external delivery infrastructure.

## Planned behavior

- Creators receive notifications when another user comments on or reacts to their video.
- Channel owners receive notifications when another user subscribes.
- Users never receive notifications for their own activity or for removals and unsubscribe actions.
- An authenticated inbox shows newest notifications first with unread state.
- Users can mark one notification or all notifications as read.
- The navigation displays the current user's unread count.

## Acceptance criteria

- Every query and mutation is scoped to `request.user`.
- Anonymous users are redirected to login.
- Cross-user read mutations return 404 without changing data.
- Notification mutations accept POST only and retain CSRF protection.
- Notification creation is isolated in a service module.
- The feature introduces no email, push, background workers, polling, or paid services.

## Architecture

`Notification` will store recipient, optional actor, event kind, optional video or channel target, creation time, and read time. `video/services/notifications.py` will create event records and keep self-notification rules out of views. A context processor will provide only the authenticated user's unread count to navigation.

## Test plan

Focused tests will cover event creation, self-event suppression, unsubscribe/removal behavior, inbox privacy and ordering, unread counts, POST-only mutations, cross-user protection, and empty states.

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

## Out of scope

- Email, browser push, SMS, and mobile push
- Real-time sockets and polling
- Notifications for new uploads until videos explicitly belong to channels
- User notification preferences and digest schedules
- Background workers and external message brokers
