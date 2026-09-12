# Playlist Pagination Sprint

## Goal
Keep large playlists usable by paging their visible videos instead of rendering the entire collection at once.

## Scope
- Paginate visible playlist items at 24 videos per page.
- Preserve playlist item ordering across pages.
- Keep owner-only edit, delete, and remove controls unchanged.
- Continue hiding videos the current viewer cannot access.
- Keep public, unlisted, and private playlist access semantics unchanged.

## Acceptance criteria
- A playlist page renders at most 24 visible videos at once.
- Older/later playlist items are reachable through Previous/Next navigation.
- Invalid page values fall back safely through Django's paginator behavior.
- Hidden or otherwise inaccessible videos do not count as visible page items.
- Owners can still remove an item from any displayed page.
- Empty playlists keep the existing empty state.

## Architecture
- Use Django `Paginator` in `playlist_detail`; no schema or service changes are required.
- Paginate the already visibility-filtered `PlaylistItem` queryset.
- Reuse the existing playlist card markup and owner controls.

## Out of scope
- Drag-and-drop or manual reordering.
- Playlist search/filtering.
- Infinite scroll.
- Collaborative playlists.
- Schema changes, new packages, workers, external services, AWS resources, or paid infrastructure.

## Validation
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- focused playlist tests
- full test suite
