# Shorts Playback State Ownership Sprint

## Goal

Remove duplicate ownership of play/pause accessibility attributes between the main Shorts feed controller and the dedicated playback accessibility helper.

## Scope

- Keep the main feed controller responsible for playback mechanics and the visible paused-state class/text.
- Keep `shorts_playback_accessibility.js` solely responsible for the dynamic play/pause accessible name and removal of `aria-pressed`.
- Add a focused regression test that prevents the main feed controller from reintroducing playback ARIA mutations.

## Acceptance criteria

- The main Shorts feed controller no longer sets `aria-label` or `aria-pressed` on the play/pause button.
- The accessibility helper continues to expose `Play <title>` / `Pause <title>` and removes `aria-pressed`.
- Visible Play/Pause text and paused-state styling remain unchanged.
- Playback, scrolling, keyboard controls, sound, comments, reactions, subscriptions, and sharing remain unchanged.
- No schema, migration, dependency, cloud, paid service, worker, queue, AWS, or Terraform changes.

## Verification

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_playback_single_owner video.test_shorts_playback_accessibility video.test_shorts_playback_controls
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope

- Further decomposition of the main Shorts feed controller.
- Playback behavior changes.
- Backend changes.
