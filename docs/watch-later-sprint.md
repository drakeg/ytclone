# Watch Later Sprint

## Goal
Give signed-in viewers a simple private queue for whole videos they want to watch later, distinct from timestamp-based Saved moments.

## Scope
- Add a private Watch Later collection for each viewer on demand.
- Let viewers add or remove a visible video from its watch page.
- Add a dedicated Watch Later page using the existing video-card presentation.
- Add Watch Later to authenticated primary navigation.
- Preserve centralized video visibility rules so inaccessible videos never render in the queue.
- Reuse the existing private playlist persistence instead of adding duplicate schema.

## Acceptance criteria
- Anonymous viewers cannot modify or view a Watch Later collection.
- Adding the same video repeatedly is idempotent and never creates duplicates.
- Removing a video affects only the current viewer's Watch Later collection.
- The watch-page action accurately reflects whether the current video is already saved.
- The Watch Later page displays only videos the viewer can currently access.
- Saved moments remain unchanged and continue to represent timestamp bookmarks.
- The collection remains private.

## Architecture
- `video/services/watch_later.py` owns the reserved private collection and add/remove/list behavior.
- The reserved collection uses the existing `Playlist`/`PlaylistItem` persistence with the name `Watch Later` and private visibility, avoiding a redundant model and migration.
- `video/watch_later_views.py` keeps HTTP concerns thin and requires authentication.
- Existing `Video.objects.visible_to(user)` remains authoritative for rendering queued videos.

## Out of scope
- Timestamp bookmarks/Saved moments changes.
- Automatic queue cleanup based on watch completion.
- Ordering/reordering controls.
- Shorts-specific Watch Later UX.
- Infinite scroll.
- New packages, workers, external services, AWS resources, or paid infrastructure.

## Validation
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- focused Watch Later tests
- full test suite
