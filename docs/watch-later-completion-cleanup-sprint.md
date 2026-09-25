# Watch Later Completion Cleanup Sprint

## Goal

Let viewers clean completed videos out of their private Watch Later queue using the same completion rule already used by Continue Watching.

## Completion rule

A video is considered completed when the viewer has a known positive duration and five seconds or less remain:

`duration_seconds - playback_position_seconds <= 5`

This intentionally matches the existing Continue Watching cutoff so the two features do not disagree about whether a video is effectively finished.

## Scope

- Add a reusable service query for completed Watch Later videos.
- Show a "Remove watched" action only when the current viewer has completed, currently visible videos in Watch Later.
- Add a POST-only cleanup endpoint that removes all such videos from the current viewer's Watch Later playlist.
- Keep incomplete videos, videos with unknown duration, other users' queues, and inaccessible videos untouched.
- Preserve active search, sort, and page state after cleanup.
- Keep manual single-item and selected-item removal unchanged.
- Add focused regression coverage.

## Acceptance criteria

1. Completed Watch Later videos are identified using the same five-second threshold as Continue Watching.
2. Unknown-duration and incomplete videos are never removed.
3. Cleanup affects only the signed-in viewer's private Watch Later playlist.
4. Inaccessible Watch Later items are not removed by this visible-list cleanup action.
5. Search, sort, and page state are preserved after cleanup.
6. The endpoint rejects GET.
7. The cleanup action is not shown when there is nothing eligible to remove.
8. No schema, migration, dependency, worker, queue, external-service, AWS, paid-service, or Terraform changes.
9. Focused and full CI pass before readiness.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_watch_later video.test_continue_watching
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```
