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
- Use Django `Paginator` in the focused `video/playlist_views.py` detail view.
- Paginate the already visibility-filtered `PlaylistItem` queryset.
- Route only playlist detail through the focused module; existing playlist mutation behavior remains unchanged.
- Reuse the existing playlist card markup and owner controls.

## Out of scope
- Drag-and-drop or manual reordering.
- Playlist search/filtering.
- Infinite scroll.
- Collaborative playlists.
- Schema changes, new packages, workers, external services, AWS resources, or paid infrastructure.

## Validation
GitHub Actions run `34673881260` passed against the current PR/base merge state:
- dependency installation — passed.
- `python manage.py check` — passed.
- `python manage.py makemigrations --check --dry-run` — passed; no migration drift.
- `python manage.py test --parallel 4` — passed.

Focused coverage in `video/test_playlists.py` verifies the 24-item boundary, playlist order across pages, visibility filtering before pagination, page navigation, and safe invalid-page handling.
