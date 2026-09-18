# Saved moments search sprint

## Goal

Help viewers find a previously saved playback moment without paging through a large private bookmark collection.

## Scope

- Add a server-rendered search field to the authenticated Saved moments page.
- Match the viewer's visible saved moments by bookmark label or video title.
- Apply search before the existing 24-item pagination.
- Preserve the search query through Previous/Next links.
- Preserve the search query and current page when removing a bookmark from the Saved moments list.
- Keep newest-saved-first ordering, centralized video visibility, timestamp links, and watch-page bookmark behavior unchanged.
- Add focused search, pagination-state, visibility, empty-state, and redirect regression coverage.

## Acceptance criteria

1. `?q=` searches bookmark labels and video titles case-insensitively.
2. Blank/whitespace-only queries behave like the existing unfiltered Saved moments list.
3. Search operates only on `get_visible_bookmarks(user)`, so inaccessible videos remain excluded.
4. Search is applied before pagination.
5. Pagination links retain the normalized query.
6. Removing a bookmark from the list returns to the same page/query when supplied.
7. A search with no matches shows a search-specific empty state.
8. Django checks, migration drift checks, and the full test suite pass.

## Exclusions

- Full-text/ranked search infrastructure.
- Search suggestions or JavaScript autocomplete.
- Reordering or bulk bookmark actions.
- Watch Later or watch-history changes.
- Schema changes or new dependencies.
- External services, workers, AWS, or paid infrastructure.

## Architecture

Keep visibility and ordering centralized in `services.bookmarks.get_visible_bookmarks`. The focused bookmark list view normalizes a bounded query string and applies a Django `Q` filter for bookmark label/video title before `Paginator`. Redirect and pagination query strings are encoded rather than interpolated as arbitrary URLs.

## Validation

CI must run Django configuration checks, migration drift checks, and the complete test suite. The PR remains draft until those checks are green.

Local verification, with and without Docker:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_bookmarks
python manage.py test --parallel 4
docker compose run --build --rm test
```
