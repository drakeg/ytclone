# Creator Video Search Sprint

## Goal

Help creators quickly find videos in a growing library while preserving the existing publication filter, pagination, and bulk-action return context.

## Scope

- Add creator-library search across video title, description, channel name, and category name.
- Apply search and publication-status filtering before pagination.
- Preserve the active search term in publication-filter links.
- Preserve search and status in pager links.
- Reset to page 1 when changing the search term or publication status.
- Preserve search/status/page after valid bulk publication actions through the existing safe return target.
- Trim surrounding whitespace from search input.
- Keep owner scoping, trashed-video exclusion, moderation restrictions, newest-first ordering, Shorts badges, and edit/create-short actions unchanged.

## Acceptance criteria

1. Search matches title, description, channel name, and category name case-insensitively.
2. Blank/whitespace-only search behaves like no search.
3. Search and publication status combine before pagination.
4. Pager links preserve search and status.
5. Publication-status links preserve search but reset page.
6. Search submission preserves status but resets page.
7. Bulk publication updates return to the same safe search/status/page.
8. Foreign or trashed videos never become visible through search.
9. No schema, migration, dependency, worker, queue, AWS resource, paid service, or live-payment change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_management video.test_creator_video_pagination video.test_creator_video_search
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Search ranking
- Full-text search infrastructure
- Sorting controls
- Date filters
- Bulk scheduling
- Trash search
- Background jobs
