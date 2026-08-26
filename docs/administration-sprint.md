# Site and Creator Administration Sprint

## Goal

Add clear administration surfaces for two different trust boundaries: staff who moderate the entire site, and creators who manage moderation and audience information only for channels they control.

## Scope

### Site administration

- Add a staff-only site operations dashboard inside the application.
- Show bounded overview counts for users, channels, videos, comments, hidden comments, and active paid memberships.
- Show recent comments across the entire site with staff-only hide/restore actions.
- Link trusted staff to Django admin for deeper model-level operations.
- Expand Django admin registration for core video/community/monetization models so a superuser has practical whole-site access.

### Creator administration

- Change creator comment moderation from exact video-author ownership to channel-aware creator/editor scope, so channel owners can moderate comments on editor-uploaded videos.
- Add a creator Audience page that shows free subscribers and paid membership subscriptions for channels the creator owns.
- Paid membership information is read-only in this sprint; creator-side cancellation/refund/removal is deferred until it can use the payment lifecycle safely.
- Keep channel editors out of paid-member/accounting data unless they own the channel.

## Acceptance criteria

- Non-staff users cannot access the site operations dashboard or its moderation endpoints.
- Staff can hide/restore comments from any channel through the site dashboard.
- Site moderation actions are POST-only and constrained to supported moderation actions.
- Creator comment moderation includes videos in channels the user owns or edits, while excluding unrelated channels.
- Channel owners can see their own channels' free subscribers and paid membership status/tier/start date.
- Editors cannot view the owner-only Audience/member page unless they also own the channel.
- Existing viewer privacy boundaries for history, progress, watch telemetry, and bookmarks remain unchanged.
- No creator can alter Stripe/provider subscription state in this sprint.
- No schema migration, external service, AWS resource, paid infrastructure, or Terraform change is required.

## Out of scope

- Site-wide user suspension/bans
- Content strikes or appeals
- Automated abuse detection
- Creator-initiated paid membership cancellation/refunds
- Creator access to private viewer history/bookmarks/watch telemetry
- Fine-grained custom staff roles beyond Django staff/superuser permissions
- Email/push moderation alerts

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_administration
python manage.py test
docker compose run --build --rm test
```
