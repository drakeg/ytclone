# Video Trash Pagination Sprint

## Goal

Keep Video Trash usable as recoverable deletions accumulate, without changing retention, ownership, restore, or permanent-delete rules.

## Scope

- Paginate Video Trash at 25 videos per page.
- Preserve newest-deleted-first ordering.
- Keep Trash owner-scoped.
- Preserve the current safe Trash page after successful permanent deletion.
- Carry the current Trash path into the permanent-delete confirmation flow.
- Reject unsafe external return targets with a fallback to Video Trash.
- Keep restore behavior unchanged: restored videos return to My Videos as drafts.
- Keep the 30-day retention rule and media-preservation behavior unchanged.

## Acceptance criteria

1. Video Trash renders at most 25 videos per page.
2. Pager links expose Previous/Next and current page.
3. Invalid page values fall back safely using Django paginator behavior.
4. Foreign users' trashed videos never appear.
5. Permanent deletion can return to the originating safe Trash page.
6. Unsafe return targets fall back to Video Trash.
7. Restore still redirects to My Videos and returns the video as a draft.
8. No schema, migration, dependency, worker, queue, AWS resource, paid service, or live-payment change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_trash video.test_video_trash_pagination
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Trash search
- Bulk restore
- Bulk permanent deletion
- Retention-policy changes
- Automatic purge jobs
- Media-object deletion
