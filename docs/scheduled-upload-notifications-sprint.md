# Scheduled Upload Notification Sprint

## Goal

Deliver subscriber notifications when a scheduled video actually becomes visible, without requiring a worker, cron service, queue, or paid infrastructure.

## Design

Scheduled publication already transitions at request time through `Video.objects.visible_to(user)`. Notification delivery will follow the same low-cost model: an idempotent service detects due scheduled videos that have not had subscriber upload notifications delivered, marks delivery once, and creates the existing in-app upload notifications.

The service can be invoked from ordinary application traffic and from an explicit management command. This keeps correctness testable and gives operators a deterministic catch-up path without requiring always-on background infrastructure.

## Acceptance criteria

- Immediate published uploads continue notifying subscribers exactly once.
- A future scheduled video does not notify subscribers before `publish_at`.
- Once a scheduled video is due, subscriber upload notifications are delivered at most once.
- Repeated delivery attempts are idempotent and do not duplicate notifications.
- Draft, unlisted, trashed, and not-yet-due videos are ignored.
- The creator never receives their own upload notification.
- Delivery uses the existing in-app `Notification.Kind.UPLOAD` model; no email/push provider is introduced.
- A management command provides an explicit catch-up/delivery path.
- No external worker, queue, cron service, AWS resource, paid service, or Terraform change is required.

## Out of scope

- Email or push notifications
- Per-subscriber notification preferences
- Digest notifications
- External scheduling infrastructure
- Notification delivery for member-only public-release transitions
- Terraform changes

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_scheduled_upload_notifications
python manage.py test
docker compose run --build --rm test
```
