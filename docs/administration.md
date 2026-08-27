# Site and Creator Administration

VideoShare separates global site administration from creator/channel administration.

## Global site staff

Users with Django `is_staff=True` get a **Site admin** link in the application navigation and can open `/videos/site-admin/`.

The site operations dashboard provides whole-site counts plus recent videos, users, comments, community posts/replies, and moderation history. Staff can perform reversible moderation actions directly from this page:

- take down or restore a video;
- suspend or reactivate an ordinary user account;
- hide or restore comments;
- hide or restore community posts;
- hide or restore community replies.

Every staff moderation action requires a reason and records the acting staff user, action, target type/id, reason, and timestamp in `ModerationAuditEvent`.

Video takedowns preserve the video's original publication state and keep the video private until staff explicitly restore it. Creator edits and bulk publication cannot override an active staff takedown.

User suspension uses Django's existing `is_active` authentication state. The in-app moderation path blocks staff from suspending themselves and blocks superuser suspension. It does not delete the user or mutate Stripe/payment records.

Superusers retain Django's full permission model. The expanded Django admin registers the core video, channel, comment, community, playlist, notification, metadata, watch, monetization, moderation-state, and audit models.

Create a full administrator with:

```bash
python manage.py createsuperuser
```

Existing users can be promoted through Django admin or the Django shell by setting `is_staff`; use `is_superuser` only for users who should have unrestricted Django permissions.

## Creator moderation

The Creator Studio **Comments** page is channel-aware. A creator can moderate comments when either they authored the video or the video belongs to a channel they own/have accepted editor access to.

Channel owners and accepted editors can also hide or restore community replies on channels they administer. Hidden replies remain visible to those moderators with a clear hidden indicator, but are omitted for ordinary viewers. Hiding a featured reply automatically removes its featured-answer status, and hidden replies cannot be re-highlighted until restored.

Creators cannot perform site-level user sanctions or staff takedowns and cannot moderate unrelated channels.

## Creator Audience page

Channel owners get an **Audience** page in Creator Studio showing free subscribers and paid membership username/tier/status/start time. Paid membership lifecycle state remains read-only: creators cannot directly force Stripe/provider cancellations, refunds, or subscription mutations from this page.

Editors do not receive owner-level paid audience/accounting visibility solely because they can edit channel content.

## Privacy boundaries

Administration does not expose private viewer watch history, playback progress, watch-event telemetry, bookmarks, or personalized recommendation signals to creators. Site superusers may have database-level access through Django admin as part of trusted platform operations, but those signals are not surfaced as creator administration data.

## Deferred moderation work

Channel-wide suspension is intentionally deferred until it can be applied consistently across every channel surface. Reports/appeals, automated abuse detection, IP/device bans, sanction email delivery, and payment-provider sanctions also remain deferred.
