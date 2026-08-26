# Moderation Sanctions and Audit Sprint

## Goal

Give trusted site staff reversible moderation controls for videos, channels, community content, and user accounts, while giving creators scoped community moderation for their own channels. Every site-level action must require a reason and leave an audit record.

## Principles

- Prefer reversible hidden/suspended states over deletion.
- Site staff actions require a non-empty reason and are audited with actor, action, target, reason, and timestamp.
- Creator controls never cross channel boundaries and never expose private viewer history, bookmarks, or recommendation signals.
- Payment data and Stripe/provider state remain untouched by moderation actions.
- Existing publication/member visibility remains centralized; moderation adds an additional deny layer.

## Scope

- Staff can take down/restore a video.
- Staff can suspend/restore a channel.
- Staff can hide/restore community posts and replies.
- Staff can suspend/reactivate ordinary user accounts using Django's `is_active` flag, with safeguards against self-suspension and superuser suspension.
- Staff dashboard shows current moderation state and recent audit activity.
- Creators/authorized channel editors can hide/restore community replies for channels they can administer.
- Channel suspension removes that channel's videos and community posts from public/member discovery without deleting records.
- Video takedown removes the video from normal `visible_to()` surfaces without altering its publication state.

## Out of scope

- Permanent deletion by moderators
- Automated abuse detection
- Reporting/appeals workflow
- IP/device bans
- Email notifications about sanctions
- Stripe account suspension or membership cancellation
- Terraform/AWS changes

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_moderation_sanctions
python manage.py test --parallel 4
docker compose run --build --rm test
```
