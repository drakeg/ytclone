# Creator Video Pagination Sprint

## Goal

Keep the creator video library usable as the number of uploaded videos grows, while preserving the creator's current publication filter/page after bulk state changes.

## Scope

- Paginate the creator video library at 25 videos per page.
- Apply the existing publication-status filter before pagination.
- Preserve the selected publication status in pager links.
- Reset to page 1 when changing publication-status filters.
- Preserve the current safe publication status/page after valid bulk publication actions.
- Validate bulk-action return targets with the existing same-host navigation helper.
- Keep owner scoping, trashed-video exclusion, moderation-state restrictions, newest-first ordering, Shorts badges, and edit/create-short actions unchanged.

## Acceptance criteria

1. My Videos renders at most 25 videos per page.
2. Publication status filtering occurs before pagination.
3. Pager links preserve the selected publication status.
4. Status-filter links intentionally reset pagination.
5. Bulk publication updates return to the current safe filter/page.
6. Unsafe external return targets fall back to My Videos.
7. Foreign, trashed, and moderated videos retain their existing protection.
8. No schema, migration, dependency, worker, queue, AWS resource, paid service, or live-payment change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_management video.test_creator_video_pagination
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Creator-library search
- Sorting controls
- Date filters
- Bulk scheduling
- Trash pagination
- Background jobs
