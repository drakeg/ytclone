# Video Browse Sprint

## Goal
Turn the discovery homepage's small curated shelves into useful entry points for browsing the full visible long-form catalog.

## Scope
- Add a public `/videos/browse/` page for long-form videos.
- Support three browse orders matching the homepage shelves: newest, most viewed, and most liked.
- Paginate browse results at 24 videos per page.
- Reuse `Video.objects.visible_to(request.user)` so publication, membership, deletion, and moderation visibility remain centralized.
- Add "See all" links to the Newest videos, Most viewed, and Most liked homepage sections.
- Preserve the selected sort across pagination.

## Acceptance criteria
- Anonymous and authenticated viewers can browse only videos visible to them.
- Shorts remain on the dedicated Shorts experience and are excluded from this browse page.
- `sort=newest`, `sort=views`, and `sort=likes` produce deterministic ordering.
- Invalid sort values fall back to newest.
- Malformed, negative, and out-of-range page values resolve safely.
- Each page contains at most 24 videos.
- Homepage shelf links open the corresponding browse ordering.
- No ranking or visibility logic is duplicated outside the existing model/service policies.

## Architecture
- Add a focused `video/services/video_browse.py` query helper.
- Add a thin `video/discovery_views.py` browse view responsible for pagination/rendering.
- Reuse the existing `_video_cards.html` partial for results.
- Keep the homepage's existing four-item curated shelf behavior unchanged.

## Validation
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test video.test_video_browse`
- `python manage.py test`
- CI must pass before the PR leaves draft.

## Out of scope
- Infinite scroll.
- Client-side filtering.
- Shorts browsing changes.
- Personalized browse ranking.
- Schema changes, new dependencies, external services, AWS resources, or paid infrastructure.
