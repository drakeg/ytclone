# Watch Later Search Sprint

## Goal

Make a growing private Watch Later queue easier to use by letting signed-in viewers filter saved videos by title without changing queue ownership, visibility, or save/remove semantics.

## Scope

- Add an optional `q` title search to the Watch Later page.
- Apply video visibility rules and the title filter before pagination.
- Preserve the active search query through Previous/Next pagination.
- Preserve the active search query when a viewer removes an item from the filtered queue.
- Add focused regression coverage and keep the full-suite/Docker verification path documented.

## Acceptance criteria

1. Only the signed-in viewer's Watch Later queue is searched.
2. Search is case-insensitive and matches video titles.
3. Videos no longer visible to the viewer remain excluded before filtering and pagination.
4. The existing 24-video page size and newest-saved-first ordering remain unchanged.
5. Pagination links preserve the active query.
6. Removing a result returns to the current filtered page/query when it remains valid.
7. Empty or whitespace-only queries behave like the unfiltered Watch Later queue.
8. Django checks, migration-drift checks, focused tests, and the complete suite pass before the PR is ready.

## Local verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_watch_later
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Reordering Watch Later.
- Searching descriptions, tags, hashtags, creators, or channels.
- Completion-based cleanup or bulk deletion.
- Schema or migration changes.
- External services, workers, queues, AWS resources, paid services, or Terraform changes.
