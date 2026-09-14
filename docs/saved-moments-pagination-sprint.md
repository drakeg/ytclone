# Saved Moments Pagination Sprint

## Goal
Keep the private Saved moments library usable as bookmark history grows by paging visible bookmarks instead of rendering the entire collection at once.

## Scope
- Paginate the authenticated viewer's visible saved moments at 24 per page.
- Preserve existing newest-saved-first ordering.
- Continue filtering inaccessible videos before pagination.
- Preserve the current page when removing a bookmark from the Saved moments list.
- Keep bookmark creation from the watch page unchanged.
- Keep timestamp bookmark labels and seek behavior unchanged.

## Acceptance criteria
- Saved moments renders at most 24 visible bookmarks per page.
- Older bookmarks are reachable through Previous/Next navigation.
- Invalid page values fall back safely and out-of-range page values resolve to the last page through Django paginator behavior.
- Bookmarks for inaccessible videos are excluded before pagination.
- Other users' bookmarks never appear or become mutable.
- Removing a bookmark from the list returns the viewer to the same page when possible.
- Empty-state behavior remains intact.

## Architecture
- Use Django `Paginator` with a page size of 24 around `get_visible_bookmarks(user)`.
- Keep centralized visibility enforcement in `video/services/bookmarks.py`.
- Route list/delete handling through a focused bookmark view module while leaving watch-page bookmark creation unchanged.
- Pass the current page through list removal forms so redirects preserve context.
- No schema or dependency changes.

## Out of scope
- Bookmark search or filtering.
- Bookmark reordering.
- Bulk delete or retention policies.
- Changes to Watch Later or watch history.
- New packages, workers, external services, AWS resources, or paid infrastructure.

## Validation
GitHub Actions run `34798267150` on implementation head `04c63e83219cb69a39293d28406c270e8aacf81c` passed:
- `python manage.py check` — no issues.
- `python manage.py makemigrations --check --dry-run` — no changes detected.
- `python manage.py test --parallel 4` — 661 tests passed, 1 skipped.

The final documentation-only head must pass the same CI workflow before the PR is marked ready for review.
