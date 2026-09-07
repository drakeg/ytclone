# Subscription Notification Preferences Sprint

## Goal
Let viewers stay subscribed to a channel without being forced to receive every new-upload notification.

## Scope
- Add a per-user, per-channel upload-notification preference for subscriptions.
- Default existing and new subscriptions to upload notifications enabled unless the viewer explicitly turns them off.
- Add an authenticated POST endpoint to toggle upload notifications for a channel the viewer already follows.
- Show the notification preference beside the Subscribe/Unsubscribe control on channel pages.
- Apply the preference to immediate and scheduled upload notifications.
- Remove stale preference rows when a viewer unsubscribes.

## Acceptance criteria
- Only authenticated subscribers can change a channel notification preference.
- Channel owners cannot create subscription preferences for their own channel.
- Disabling upload notifications does not unsubscribe the viewer.
- Re-enabling notifications resumes future upload notices only; past notices are not backfilled.
- Existing subscribers without a stored preference continue receiving upload notifications.
- Immediate and scheduled uploads honor the same preference rule.
- Unsubscribing removes any stored preference.
- Existing subscription AJAX behavior remains compatible.

## Architecture
- Add `SubscriptionNotificationPreference` keyed uniquely by user + channel.
- Preserve the existing `Channel.subscribers` many-to-many relation as the source of subscription truth.
- Treat a missing preference row as enabled for backward compatibility.
- Keep notification filtering in `video/services/notifications.py`.
- Keep mutation logic in `video/subscription_views.py` and use the existing channel-access policy.

## Local validation
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test video.test_subscription_notification_preferences`
- `python manage.py test --parallel 4`
- `docker compose run --build --rm test`

## Out of scope
- Email, push, SMS, or browser notifications.
- Per-video or per-topic notification rules.
- Notification digests or schedules.
- Changing creator-facing subscription notifications.
- External services, workers, AWS resources, or paid infrastructure.
