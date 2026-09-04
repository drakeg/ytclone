# Search Filters Sprint

## Goal

Let viewers narrow an existing search without adding a new search backend or changing the current ranking and visibility rules.

## Scope

- Add a content-type filter for All, Standard videos, and Shorts.
- Add an upload-date filter for Any time, Today, This week, This month, and This year.
- Apply filters only to video results; channel and playlist matching remain unchanged.
- Preserve the current search query, sort option, filters, and independent pagination state in search navigation.
- Reset the video page to page 1 when the user changes a filter or sort option through the search form.
- Reuse `Video.objects.visible_to(user)` and the existing `search_content()` query composition.
- Keep the implementation server-rendered and dependency-free.
- Add focused service/view/template tests for filtering, invalid values, visibility, and pagination-link preservation.

## Acceptance criteria

- `content=video` excludes rows with `VideoShort` metadata.
- `content=short` returns only rows with `VideoShort` metadata.
- Invalid content values safely fall back to All.
- Date filters use the video's existing `pub_date` and timezone-aware boundaries.
- Invalid date-filter values safely fall back to Any time.
- Existing search ranking and sort orders are unchanged inside the filtered result set.
- Channel and playlist result sets are unaffected by video filters.
- Pagination links preserve the selected content/date filters.
- Existing private/unlisted/member visibility behavior remains unchanged.
- No schema migration, external service, new dependency, worker, queue, or paid service is added.

## Architecture

- `video/services/search.py` owns filter normalization and applies filters to the already-visible video queryset.
- `SearchResults` carries the normalized filter values so the HTTP/template layer can render canonical state.
- `video/search_views.py` forwards request filter parameters and continues to own bounded result pagination.
- `video/templates/videos/search_results.html` exposes compact select controls in the existing search controls area and preserves filter values in pagination links.

## Date filter semantics

The date filter compares `pub_date` against a timezone-aware lower bound calculated from `timezone.now()`:

- Today — start of the current local day.
- This week — seven days before the current time.
- This month — start of the current local month.
- This year — start of the current local year.

These choices keep the first version deterministic and inexpensive while remaining useful for typical search refinement.

## Validation

GitHub Actions run `33829250341` passed on the completed implementation head:

- `python manage.py check` — passed.
- `python manage.py makemigrations --check --dry-run` — passed.
- `python manage.py test --parallel 4` — passed.

The documentation-only closeout commit remains subject to the same checks before the pull request is marked ready for review.

## Out of scope

- Duration filtering (video duration is not currently stored on the `Video` row).
- Search-history persistence.
- Category/channel-specific facets.
- Fuzzy matching or typo correction.
- Changes to relevance weights.
- Infinite scroll or client-side result fetching.
