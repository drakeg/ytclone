# Watch Later Manual Order Sprint

## Goal
Let a viewer deliberately arrange videos in their private Watch Later queue without changing the existing newest, oldest, or title sorts.

## Scope and design
- Add an opt-in `Manual order` sort based on existing `PlaylistItem.position`, with stable added-at/ID tie-breakers.
- Show Move up/down POST controls only in Manual order, on the Watch Later page, for visible saved videos.
- Reorder against adjacent *visible* saved entries, even if inaccessible items are interspersed in the playlist; retain those inaccessible entries without exposing them.
- Reuse existing playlist positions and ownership/visibility checks. Preserve current search, sort, and page parameters after moving.
- No schema change, background job, paid service, or external integration.

## Acceptance
- Manual sort is deterministic and existing sorts remain unchanged.
- Up/down moves affect only the signed-in viewer's Watch Later playlist.
- Forged, other-user, unsaved, or inaccessible video IDs are rejected.
- Boundary moves are no-ops; a hidden item between visible entries does not block a move.
- Search is a display filter; reorder operates among the complete visible queue, not only search matches.
- GET cannot mutate state. UI exposes no move controls outside Manual order.
- Focused, full, and Compose Django checks pass.

## Exclusions
Drag/drop ordering, changing standard playlist ordering, automatic completion cleanup, migration work, and paid infrastructure.

## Verification
```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_watch_later video.test_playlist_reordering
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```
