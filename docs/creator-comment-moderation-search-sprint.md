# Creator Comment Moderation Search Sprint

## Goal

Help creators find specific comments in a large moderation queue without weakening existing owner/editor scoping or moderation safeguards.

## Scope

- Add a text search field to the creator comment moderation queue.
- Match case-insensitively against comment text, author username, and video title.
- Apply search and the existing All / Visible / Hidden filter before pagination.
- Preserve the active search term when switching status filters.
- Preserve search and status in pager links.
- Reset to page 1 when changing the search term or status.
- Preserve the current search/status/page after valid bulk hide/restore actions through the existing safe return target.
- Trim surrounding whitespace from search input.
- Keep newest-first ordering, channel-editor access, trashed-video exclusion, and forged-ID protection unchanged.

## Acceptance criteria

1. Search matches comment text, author username, and video title case-insensitively.
2. Blank/whitespace-only search behaves like no search.
3. Search and status filter combine before pagination.
4. Pager links preserve search and status.
5. Status links preserve search but reset page.
6. Search submission preserves status but resets page.
7. Bulk moderation returns to the same safe search/status/page.
8. Foreign and trashed comments never become searchable or mutable outside existing authorization.
9. No schema, migration, dependency, worker, queue, AWS resource, paid service, or live-payment change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_comment_moderation video.test_creator_comment_pagination video.test_creator_comment_search
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Automated moderation
- Search ranking
- Regex/full-text search infrastructure
- Date-range filters
- Comment deletion
- Background jobs
