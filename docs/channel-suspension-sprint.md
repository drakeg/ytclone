# Channel Suspension Sprint

## Goal

Give trusted site staff a reversible, reason-required way to suspend an entire channel while ensuring suspended channels cannot leak through viewer-facing video, discovery, community, or paid-membership access paths.

## Design

Channel suspension is a moderation overlay, not deletion. A one-to-one moderation state records the active suspension while `ModerationAuditEvent` records suspension/restoration actions and reasons. Existing content and membership rows remain intact so staff can restore the channel without reconstructing data.

The central video visibility boundary (`Video.objects.visible_to(user)`) will exclude suspended channels for everyone except trusted site staff. Channel/community views will use a shared channel-availability helper so direct URLs cannot bypass the sanction. Paid membership entitlement checks will not unlock content from a suspended channel.

## Acceptance criteria

- Staff can suspend and restore a channel only with a non-empty moderation reason.
- Every actual suspension/restoration creates a moderation audit event.
- Suspended-channel videos disappear from public/search/discovery querysets that use `visible_to()`.
- Active paid members do not retain playback access to suspended-channel videos.
- Suspended channel and community pages are unavailable to ordinary viewers through direct URLs.
- The channel owner/editor cannot bypass the suspension through creator-facing publication controls.
- Trusted site staff can still inspect suspended content for moderation/review.
- Suspension does not delete videos, community content, subscribers, paid membership rows, transactions, or creator data.
- Restoring the channel makes otherwise-valid content available again without rebuilding it.

## Out of scope

- Canceling/refunding Stripe subscriptions automatically
- Deleting a channel or its content
- Automatic suspension based on reports or thresholds
- Appeals workflow
- Email/push notices
- Terraform/AWS changes

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_channel_suspension
python manage.py test --parallel 4
docker compose run --build --rm test
```
