# Video Browse Filters Sprint

## Goal
Make the full long-form browse page more useful by letting viewers narrow the visible catalog by category and upload recency without leaving the browse experience.

## Scope
- Add an optional category filter to `/videos/browse/` using existing `Category` rows.
- Add an upload-date filter with Any time, Today, This week, This month, and This year.
- Preserve the current newest, most viewed, and most liked sort choices.
- Preserve selected filters across pagination and sort changes.
- Reset pagination when a viewer changes filters.
- Keep the page public and continue using the centralized video visibility policy.

## Acceptance criteria
- Anonymous and authenticated viewers only see videos already allowed by `Video.objects.visible_to(user)`.
- Shorts remain excluded from the long-form browse page.
- Selecting a category returns only videos in that category.
- Unknown category values fall back safely to All categories.
- Upload-date filters use timezone-aware boundaries and reject invalid values by falling back to Any time.
- Category and upload-date filters combine with all three existing sort modes.
- Pagination links preserve sort, category, and upload-date state.
- Changing a sort or filter starts from the first result page.
- The page remains bounded at 24 videos per page.

## Architecture
- Extend `video/services/video_browse.py`; keep filtering and normalization out of the view/template.
- Reuse the existing `Category` model; no schema change.
- Keep `video/discovery_views.py` thin and responsible only for request parsing, pagination, and context.
- Reuse the current browse template and `_video_cards.html` partial.

## Local validation
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test video.test_video_browse_filters`
- `python manage.py test --parallel 4`
- `docker compose run --build --rm test`

## Out of scope
- Shorts filters.
- Duration or resolution filters.
- Channel facets.
- Search relevance changes.
- Infinite scroll or client-side filtering.
- Schema changes, new packages, external services, workers, AWS resources, or paid infrastructure.
