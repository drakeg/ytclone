# Shorts Playback Accessibility Sprint

## Sprint goal

Make the immersive Shorts play/pause control expose a single, consistent accessible state while preserving existing playback behavior.

## Scope

- Keep the action-oriented accessible label (`Play <title>` / `Pause <title>`).
- Remove `aria-pressed` from the play/pause command button after the feed initializes and whenever playback state changes.
- Keep mute/unmute as a toggle control with its existing `aria-pressed` state.
- Scope the enhancement to the Shorts feed.
- Add focused regression coverage.

## Why

The existing play/pause button changes both its visible/action label and `aria-pressed`. That mixes command-button and toggle-button semantics and can announce a confusing state to assistive technology. A play/pause command is clearer when the accessible name describes the action currently available.

## Acceptance criteria

- Play/pause continues to work through the button, video click, keyboard Space shortcut, autoplay, and pause events.
- The play button accessible label follows the actual video state.
- `aria-pressed` is not retained on the play/pause control after initialization or playback-state events.
- The mute button keeps its toggle semantics and `aria-pressed` state.
- No schema, migration, backend, playback, cloud, paid-service, or dependency changes.

## Test plan

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_playback_accessibility video.test_shorts_playback_controls
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope

- Playback UI redesign.
- Keyboard shortcut changes.
- Autoplay policy changes.
- Sound preference changes.
- Extraction of the remaining inline Shorts playback JavaScript.
