# Subscriptions Feed Sprint

## Goal
Give authenticated viewers one dedicated place to browse the channels they follow and the newest videos from those subscriptions.

## Scope
- Add an authenticated `/videos/subscriptions/` page.
- Show followed channels using the existing `Subscription` relationship and centralized channel access policy.
- Show newest videos from followed channels using `Video.objects.visible_to(request.user)` so existing publication and visibility rules remain authoritative.
- Add Subscriptions to the authenticated desktop and mobile navigation.
- Provide useful empty states for viewers who follow no channels and for followed channels with no currently visible uploads.
- Keep the implementation server-rendered and bounded; no new frontend framework or background job.

## Acceptance criteria
- Anonymous visitors are redirected to login.
- Authenticated viewers only see channels they currently follow and that remain available to them.
- The feed only includes videos already visible to the viewer through the central `VideoQuerySet.visible_to` policy.
- Videos are ordered newest first and the initial page is bounded.
- The page distinguishes an empty subscription list from subscriptions that simply have no visible uploads yet.
- Desktop and mobile navigation expose the page to authenticated viewers.
- Existing subscribe/unsubscribe AJAX behavior remains unchanged.
- Focused tests cover authentication, channel filtering, video visibility/order, empty states, and navigation.

## Architecture
- Keep query composition in a focused service (`video/services/subscriptions.py`).
- Keep the view thin: authentication, service call, render.
- Reuse `available_channels(user)` and `Video.objects.visible_to(user)` rather than duplicating moderation/publication logic.
- Use the existing `Subscription` model as the source of followed channel IDs.
- Use the existing card/template styling rather than introducing a new design system.

## Local validation
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test video.test_subscriptions_feed`
- `python manage.py test`
- `docker compose run --build --rm test`

## Out of scope
- Notification preference changes.
- Email/browser subscription alerts.
- Personalized ranking or ML.
- Infinite scrolling or client-side pagination.
- Database schema changes.
- New packages, queues, workers, external services, AWS resources, or paid infrastructure.
