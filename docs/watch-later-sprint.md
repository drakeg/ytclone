# Watch Later Sprint

## Goal
Give signed-in viewers a simple private queue for whole videos they want to watch later, distinct from timestamp-based Saved moments.

## Scope
- Add a private Watch Later collection for each viewer on demand.
- Let viewers add or remove visible videos directly from shared video cards.
- Add a dedicated Watch Later page using the existing video-card presentation.
- Add Watch Later to authenticated primary navigation.
- Preserve centralized video visibility rules so inaccessible videos never render in the queue.
- Reuse the existing private playlist persistence instead of adding duplicate schema.

## Acceptance criteria
- Anonymous viewers cannot modify or view a Watch Later collection.
- Adding the same video repeatedly is idempotent and never creates duplicates.
- Removing a video affects only the current viewer's Watch Later collection.
- Video-card actions accurately reflect whether each video is already saved.
- The Watch Later page displays only videos the viewer can currently access.
- Saved moments remain unchanged and continue to represent timestamp bookmarks.
- The collection remains private.

## Architecture
- `video/services/watch_later.py` owns the reserved private collection and add/remove/list behavior.
- The reserved collection uses the existing `Playlist`/`PlaylistItem` persistence with the name `Watch Later` and private visibility, avoiding a redundant model and migration.
- `video/watch_later_views.py` keeps HTTP concerns thin and requires authentication.
- `video/templatetags/watch_later_tags.py` owns card-level saved-state rendering.
- Existing `Video.objects.visible_to(user)` remains authoritative for rendering and mutation access.

## Out of scope
- Timestamp bookmarks/Saved moments changes.
- Automatic queue cleanup based on watch completion.
- Ordering/reordering controls.
- Shorts-specific Watch Later UX.
- Infinite scroll.
- New packages, workers, external services, AWS resources, or paid infrastructure.

## Validation
GitHub Actions run `34673686469` passed on the corrected feature head:
- dependency installation — passed.
- `python manage.py check` — passed.
- `python manage.py makemigrations --check --dry-run` — passed; no migration drift.
- `python manage.py test --parallel 4` — passed.

The first full-suite run exposed an existing bookmark-ordering assertion that matched the generic word `Later` in the new navigation. That test was narrowed to the actual rendered bookmark labels (`0:05 · Sooner` and `1:30 · Later`) without changing application behavior, and the full suite then passed.
