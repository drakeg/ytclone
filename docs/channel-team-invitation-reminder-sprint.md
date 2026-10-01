# Channel Team Invitation Reminder Sprint

## Goal

Let channel owners manually remind an invited editor about a still-pending, unexpired invitation using the existing in-app notification flow and optional invitation email configuration.

## Scope

- Add an owner-only, POST-only reminder action from the channel team page.
- Allow reminders only for invitations that are still pending and not expired.
- Create a fresh in-app team-invitation notification for each explicit reminder.
- When optional invitation email is enabled, send the same safe invitation email again.
- Reuse the authenticated Team invites inbox link; do not expose invitation tokens.
- Email delivery failure must never invalidate or alter the pending invitation or in-app reminder.
- Add focused tests for ownership, POST-only behavior, pending/expiry checks, notification delivery, optional email delivery, and email failure isolation.

## Acceptance criteria

1. Only the channel owner can remind.
2. GET requests cannot send reminders.
3. Accepted, declined, revoked, and expired invitations cannot be reminded.
4. A successful reminder adds one new in-app invitation notification.
5. Optional email delivery follows the same disabled-by-default configuration as initial invitations.
6. Missing invitee email simply skips email while preserving the in-app reminder.
7. Email exceptions do not roll back the in-app reminder or alter invitation state.
8. No schema, migration, scheduler, background worker, queue, external email API, AWS, or paid-service dependency is added.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_channel_team_invitations video.test_channel_team_notifications
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

Automatic/scheduled reminders, reminder throttling, bulk reminders, HTML email, invitation tokens in email, and external provider provisioning.
