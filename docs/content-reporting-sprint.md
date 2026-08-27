# Content Reporting & Moderation Queue Sprint

## Goal

Give signed-in viewers and creators a simple way to privately report problematic site content, and give trusted staff a dedicated triage queue that can resolve or dismiss reports without exposing reporter identity to creators or other users.

## Scope

Reportable targets:

- Channels
- Videos
- Video comments/replies
- Community posts
- Community replies

Report reasons use a small controlled vocabulary plus optional details. Reports are private moderation records and never appear on creator analytics, channel pages, or public profiles.

Staff get a dedicated report queue with open/resolved/dismissed states, reviewer identity, review timestamp, and resolution notes. Staff moderation actions remain separate and continue using the existing reversible sanction/audit system.

## Acceptance criteria

- Only authenticated users can submit reports.
- A report can only be created for content the reporter can currently access through normal visibility rules.
- Users cannot report their own channel/content.
- The same user cannot create duplicate open reports for the same target.
- Report reason is required and validated; optional details are length-limited.
- Reporter identity is visible only to trusted staff.
- Creators/channel editors do not receive report details or reporter identity through creator tooling.
- Staff can filter the moderation queue by status and mark reports resolved or dismissed with a required resolution note.
- Review actions record the reviewing staff member and timestamp.
- Resolving/dismissing a report does not automatically delete content or mutate Stripe/payment state.
- Existing takedown, suspension, hide/restore, and audit actions remain independent and reusable from the staff moderation console.

## Out of scope

- Automatic sanctions based on report counts
- Reporter reputation/scoring
- Email/push notifications
- Creator-facing appeal workflow
- Machine-learning moderation
- External moderation providers
- Terraform/AWS changes

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_content_reporting
python manage.py test --parallel 4
docker compose run --build --rm test
```
