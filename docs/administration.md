# Site and Creator Administration

VideoShare separates global site administration from creator/channel administration.

## Global site staff

Users with Django `is_staff=True` get a **Site admin** link in the application navigation and can open `/videos/site-admin/`.

The site operations dashboard provides:

- whole-site counts for users, channels, active videos, comments, hidden comments, and active paid memberships;
- the 50 most recent comments across all channels;
- POST-only hide/restore moderation for those comments;
- a link to Django admin for deeper model-level operations.

Superusers retain Django's full permission model. The expanded Django admin registers the core video, channel, comment, community, playlist, notification, metadata, watch, and monetization models. Staff users who are not superusers still need ordinary Django model permissions for model-level changes inside `/admin/`; the custom site moderation dashboard itself is intentionally available to trusted staff.

Create a full administrator with:

```bash
python manage.py createsuperuser
```

Existing users can be promoted through Django admin or the Django shell by setting `is_staff`; use `is_superuser` only for users who should have unrestricted Django permissions.

## Creator moderation

The Creator Studio **Comments** page is channel-aware. A creator can moderate comments when either:

- they authored the video; or
- the video belongs to a channel they own or have accepted editor access to.

This means a channel owner can moderate comments on a video uploaded by an assigned editor without granting access to unrelated channels.

## Creator Audience page

Channel owners get an **Audience** page in Creator Studio. It shows, per owned channel:

- free channel subscribers;
- paid membership subscriber username;
- membership tier;
- membership status;
- membership start time.

The page is deliberately read-only for paid membership lifecycle state. Creators cannot directly force Stripe/provider cancellations, refunds, or subscription mutations from this page. Those actions require payment-lifecycle-safe flows and remain deferred.

Editors do not receive owner-level paid audience/accounting visibility solely because they can edit channel content.

## Privacy boundaries

Administration does not expose private viewer watch history, playback progress, watch-event telemetry, or saved bookmarks to creators. Site superusers may have database-level access through Django admin as part of trusted platform operations, but those viewer signals are not surfaced as creator analytics or creator administration data.

## Deferred moderation work

Future administration sprints can add explicit user/channel sanctions, video takedown/restore workflows, community-post/reply moderation, reports/appeals, and safe creator-side membership actions. Those should build on explicit audit and authorization rules rather than broadening this first foundation implicitly.
