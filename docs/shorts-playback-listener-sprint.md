# Shorts Playback Listener Consolidation Sprint

## Goal

Remove per-video playback listeners from the immersive Shorts feed while preserving playback behavior, visible button state, and the existing accessibility ownership boundary.

## Scope

- Delegate video click handling from the feed container.
- Delegate `play` and `pause` state synchronization from the feed container using capture because media events do not bubble normally.
- Continue using the existing Short index metadata to resolve the affected video/button pair.
- Preserve keyboard playback toggling, autoplay, IntersectionObserver activation, sound preference, reduced-motion handling, and visibility lifecycle behavior.
- Leave dynamic playback ARIA ownership in `shorts_playback_accessibility.js`.

## Boundaries

- No template, backend, database, schema, migration, dependency, FFmpeg, cloud, AWS, paid service, worker, or queue change.
- No change to feed navigation or playback policy.
- No new global event listeners.

## Acceptance criteria

- `shorts_feed.js` no longer attaches click/play/pause listeners once per video.
- Clicking a Short still toggles that Short's playback.
- Space still toggles the active Short.
- Real `play` and `pause` events still update the visible Play/Pause state.
- Existing playback accessibility delegation remains unchanged.
- Regression tests explicitly protect the delegated listener structure.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_playback_controls video.test_shorts_feed_controller
python manage.py test --parallel 4
docker compose run --build --rm test
```
