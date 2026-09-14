# Playlist Reordering Sprint

## Goal
Let playlist owners deliberately reorder videos in their playlists while preserving existing visibility, pagination, and ownership rules.

## Scope
- Add owner-only POST actions to move a playlist item one position up or down.
- Keep ordering deterministic and contiguous after a move.
- Show move controls only to the playlist owner.
- Preserve the current playlist page after a move.
- Keep inaccessible videos filtered from viewer rendering without changing their stored playlist membership.
- Put reordering logic in a focused service module and keep views thin.

## Acceptance criteria
- Only the playlist owner can reorder its items.
- Reordering is POST-only and CSRF protected through normal Django forms.
- Moving the first item up or the last item down is an idempotent no-op.
- A successful move swaps the requested item with its adjacent stored playlist item and leaves all other relative ordering unchanged.
- Repeated moves do not create duplicate positions.
- Playlist detail continues to paginate 24 visible items per page in playlist order.
- Owner controls preserve the current `page` query parameter after the action.
- Public, unlisted, and private playlist access semantics remain unchanged.

## Architecture
`PlaylistItem.position` remains the ordering source of truth. A focused `video/services/playlist_ordering.py` service owns authorization and adjacent-item swapping inside a transaction. `playlist_views.py` owns the POST endpoint and redirect. No JavaScript or new dependency is required.

## Validation
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_playlist_reordering
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope
- Drag-and-drop ordering.
- Arbitrary numeric position entry.
- Reordering Watch Later.
- Playlist collaboration or shared editing.
- Schema changes, external services, workers, AWS, or paid infrastructure.
