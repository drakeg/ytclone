# Creator Comment Moderation Pagination Sprint

## Goal

Keep the creator comment-moderation queue usable as comment volume grows and preserve the creator's current moderation context after bulk actions.

## Scope

- Paginate creator-visible moderation comments at 25 per page.
- Apply the existing All / Visible / Hidden status filter before pagination.
- Preserve the selected status filter in pager links.
- Reset to page 1 when changing status filters.
- Preserve the current status/page after valid bulk hide or restore actions.
- Validate bulk-action return targets with the existing same-host navigation helper.
- Keep creator/channel-editor scoping, trashed-video exclusion, forged-ID protection, and newest-first ordering unchanged.

## Acceptance criteria

1. Creator moderation renders at most 25 comments per page.
2. Filtering occurs before pagination.
3. Pager links preserve the selected status filter.
4. Status filter links intentionally reset pagination.
5. Bulk hide/restore returns to the current safe moderation page/filter.
6. External or malformed return targets fall back to the moderation list.
7. Foreign and trashed comment IDs remain non-mutable.
8. No schema, migration, dependency, worker, queue, AWS resource, paid service, or live-payment change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_comment_moderation video.test_creator_comment_pagination
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Search
- Author/video text filtering
- Automated moderation
- Comment deletion
- Background jobs
