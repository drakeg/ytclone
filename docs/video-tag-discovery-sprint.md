# Video Tag Discovery Sprint

## Goal
Finish the structured-tag discovery loop by making creator-entered video tags directly browsable from watch pages.

## Scope
- Add a public tag detail page for structured `Tag` metadata.
- Link structured tags on the video watch page to that tag detail page.
- Reuse `Video.objects.visible_to(request.user)` so tag browsing cannot expose restricted videos.
- Order tag results newest-first, consistent with hashtag discovery.
- Keep hashtags as a separate visible metadata system with their existing `#hashtag` routes.

## Acceptance criteria
- Clicking a structured tag opens a dedicated tag page.
- Tag pages show only videos visible to the current viewer.
- The route resolves tags case-insensitively through normalized stored names.
- Unknown tags return 404.
- Tag and hashtag routes remain distinct.
- Existing search support for tags remains unchanged.
- No schema change is required.

## Architecture
- Extend `video/metadata_views.py` with a `tag_detail` view.
- Add a `/videos/tags/<name>/` route in `video/urls.py`.
- Reuse the existing video-card partial for result rendering.
- Keep tag normalization/synchronization in the existing metadata service.

## Validation
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test video.test_tag_discovery`
- `python manage.py test --parallel 4`
- `docker compose run --build --rm test`

## Out of scope
- Tag following/subscriptions.
- Tag recommendation ranking.
- Tag autocomplete changes.
- Tag moderation/admin tooling.
- Schema changes, dependencies, external services, AWS resources, or paid infrastructure.
