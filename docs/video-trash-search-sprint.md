# Video Trash Search Sprint

## Goal

Help creators find recoverable deleted videos quickly while preserving Trash pagination, ownership, retention rules, and permanent-delete return context.

## Scope

- Add owner-scoped Trash search across video title, description, channel name, and category name.
- Apply search before pagination.
- Preserve the active query in pager links.
- Reset to page 1 when submitting a new query.
- Preserve search/page through permanent-delete confirmation and successful deletion via the existing safe return target.
- Trim surrounding whitespace and treat whitespace-only input as unfiltered.
- Keep restore behavior unchanged: restored videos return to My Videos as drafts.
- Keep newest-deleted-first ordering and 30-day retention behavior unchanged.

## Acceptance criteria

1. Trash search matches title, description, channel name, and category name case-insensitively.
2. Foreign users' trashed videos never appear through search.
3. Blank/whitespace-only search behaves like no search.
4. Search applies before 25-per-page pagination.
5. Pager links preserve the active query.
6. Search submission resets pagination.
7. Permanent-delete confirmation and POST preserve safe query/page context.
8. Unsafe external return targets still fall back to Video Trash.
9. No schema, migration, dependency, worker, queue, AWS resource, paid service, or live-payment change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_trash video.test_video_trash_pagination video.test_video_trash_search
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Search ranking
- Full-text search infrastructure
- Bulk restore
- Bulk permanent deletion
- Retention-policy changes
- Automatic purge jobs
- Media-object deletion
