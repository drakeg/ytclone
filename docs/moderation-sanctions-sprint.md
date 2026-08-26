# Moderation Sanctions and Audit Sprint

## Goal

Give trusted site staff reversible moderation controls for videos, community content, comments, and user accounts, while giving creators scoped community moderation for their own channels. Every site-level action must require a reason and leave an audit record.

## Principles

- Prefer reversible hidden/suspended states over deletion.
- Site staff actions require a non-empty reason and are audited with actor, action, target, reason, and timestamp.
- Creator controls never cross channel boundaries and never expose private viewer history, bookmarks, or recommendation signals.
- Payment data and Stripe/provider state remain untouched by moderation actions.
- Active staff takedowns cannot be overridden by creator edit/bulk-publication flows.

## Scope

- Staff can take down/restore a video while preserving its original publication state.
- Staff can hide/restore comments, community posts, and community replies.
- Staff can suspend/reactivate ordinary user accounts using Django's `is_active` flag, with safeguards against self-suspension and superuser suspension.
- Staff dashboard shows current moderation state and recent audit activity.
- Creators/authorized channel editors can hide/restore community replies for channels they can administer.
- Hidden featured replies are automatically unfeatured and cannot be highlighted until restored.

## Deferred

Channel-wide suspension was considered for this sprint but is deliberately deferred until it can be enforced consistently across channel detail, channel discovery, video discovery, search, community, memberships, and creator workflows without leaving bypasses.

## Out of scope

- Channel-wide suspension
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
python manage.py test video.test_moderation_sanctions video.test_administration
python manage.py test --parallel 4
docker compose run --build --rm test
```
