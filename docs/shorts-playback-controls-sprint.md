# Shorts Playback Controls Sprint

## Goal
Make the immersive Shorts feed feel like a purpose-built player by giving viewers direct, accessible playback and sound controls without changing backend visibility, ranking, or media processing.

## Scope
- Click/tap the active video to pause or resume playback.
- Add an explicit play/pause overlay control for keyboard and assistive-technology users.
- Let Space toggle playback when focus is on the Shorts feed rather than an interactive control.
- Carry the viewer's mute/unmute preference across Shorts for the current page session.
- Keep autoplay muted until the viewer explicitly enables sound.
- Update control labels and pressed state as playback/sound state changes.
- Preserve existing scroll-snap, keyboard navigation, reactions, subscriptions, comments, replies, reporting, and visibility behavior.

## Acceptance criteria
1. The active Short can be paused/resumed by clicking/tapping the video or its play/pause control.
2. Space toggles the active Short while feed focus is not inside another interactive element.
3. Enabling sound on one Short causes subsequently activated Shorts to use the same sound preference; disabling sound does the reverse.
4. The play/pause and mute controls expose current state with accessible labels and `aria-pressed` values.
5. Moving to another Short still pauses off-screen videos and starts the active Short.
6. Existing viewer actions and visibility rules remain unchanged.
7. No schema, migration, external API, cloud service, paid dependency, worker, queue, AWS resource, or Terraform change is introduced.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_playback_controls
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope
- Remembering sound preference across browser sessions.
- Custom seek/progress controls.
- Playback-speed selection.
- Picture-in-picture/fullscreen controls.
- Recommendation or ranking changes.
