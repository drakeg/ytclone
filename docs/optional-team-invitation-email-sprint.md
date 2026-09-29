# Optional Channel Team Invitation Email Sprint

## Goal

Optionally send a channel editor invitation email in addition to the existing private in-app invitation and notification, without requiring a paid provider or making email delivery a prerequisite for the invitation itself.

## Configuration

- `DJANGO_TEAM_INVITATION_EMAIL_ENABLED=false` by default.
- When enabled, Django email settings are environment-driven.
- The default enabled-development backend is Django's console backend, so local testing requires no external account or spend.
- SMTP can be selected explicitly through `DJANGO_EMAIL_BACKEND` and related environment variables.
- `DJANGO_DEFAULT_FROM_EMAIL` controls the sender address.

## Scope

- Add a focused email helper for newly created channel-team invitations.
- Send only when email delivery is enabled and the invitee has a non-empty email address.
- Include channel name, inviter identity, seven-day expiration, and a direct absolute link to the Team invites inbox.
- Keep the existing in-app invitation and notification authoritative.
- Email failure must not roll back, delete, or invalidate an otherwise valid invitation.
- Add tests for disabled mode, missing recipient email, successful delivery, recipient/link content, and delivery failure isolation.
- Document all new environment variables in `.env.example`.

## Acceptance criteria

1. Default behavior remains unchanged and performs no outbound email.
2. Enabling the feature with Django's console or test email backend sends one message for a newly created invitation.
3. Invitees without an email address still receive the existing in-app invitation only.
4. Delivery exceptions do not affect invitation persistence or in-app notification creation.
5. The email contains no secrets or invitation tokens; it links to the authenticated Team invites inbox.
6. Rejected duplicate invitations do not emit email.
7. No schema/migration, scheduled reminder, worker, queue, AWS, or paid-service dependency is introduced.
8. Focused and full CI pass before readiness.

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

Scheduled reminders, invitation-token login links, email verification, HTML email, bulk invitations, external email APIs, and any paid provider setup.
