# Shorts Playback Controller Hardening Sprint

## Goal

Keep the extracted Shorts playback accessibility state synchronized through feed playback events and browser tab visibility changes without changing playback behavior.

## Scope

- Delegate `play` and `pause` synchronization from the Shorts feed container instead of registering one listener pair per video.
- Re-synchronize all playback action labels when the document becomes visible again.
- Preserve the action-button accessibility contract introduced by the previous sprint: `Play <title>` / `Pause <title>` with no `aria-pressed` state.
- Preserve the mute control as a true pressed-state toggle.

## Acceptance criteria

- Shorts playback action labels remain correct after play and pause events.
- Playback state synchronization works through delegated feed listeners.
- Returning to a previously hidden tab refreshes all playback button labels.
- Playback behavior, keyboard controls, sound behavior, scrolling, reactions, comments, subscriptions, and sharing remain unchanged.
- No schema, migration, dependency, external service, cloud resource, paid service, worker, queue, AWS, or Terraform changes.

## Verification

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_playback_accessibility video.test_shorts_playback_controls
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope

- Moving the remaining large inline Shorts feed controller or CSS into static files.
- Changing autoplay, navigation, or sound semantics.
- Backend changes.
