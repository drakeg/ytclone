# Watch History Search Sprint

## Goal

Let signed-in viewers find previously watched videos by title while preserving private history ownership, video visibility, newest-first ordering, and existing pagination.

## Scope

- Add an optional `q` title search to Watch History.
- Apply current-user ownership and video visibility before search and pagination.
- Preserve the active query through Previous/Next pagination.
- Preserve the active query/page when removing one history entry.
- Keep Clear history semantics explicit: it clears the viewer's complete history, not only filtered results.
- Add focused regression coverage and retain documented Docker/non-Docker verification.

## Acceptance criteria

1. Search is login-required and only examines the current viewer's history.
2. Search is case-insensitive and matches video titles.
3. Inaccessible videos remain excluded before filtering and pagination.
4. The existing 24-entry page size and newest-watched-first ordering remain unchanged.
5. Pagination preserves `q`.
6. Removing an entry preserves the current filtered page/query.
7. Whitespace-only search behaves like the unfiltered history.
8. Clear history continues to clear all of the current viewer's history.
9. Configuration, migration-drift, focused tests, and the full suite pass before readiness.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_watch_history
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Search by creator, channel, category, tags, or date.
- Per-filter bulk deletion.
- Changes to history recording or playback progress.
- Schema/migration/dependency changes.
- External services, workers, AWS, paid services, or Terraform changes.
