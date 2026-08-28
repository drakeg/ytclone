# Immersive Shorts Feed Sprint

## Goal
Turn the existing Shorts list into a focused, one-Short-at-a-time viewing experience that feels purpose-built for short-form video while retaining the existing Django visibility, moderation, reporting, reaction, and comment flows.

## Scope
- Use a viewport-height, scroll-snap Shorts feed on supported browsers.
- Keep one Short centered at a time on desktop and mobile.
- Automatically play the active Short and pause Shorts that leave the viewport.
- Support Arrow Up / Arrow Down and Page Up / Page Down navigation.
- Preserve native touch scrolling/swiping through CSS scroll snapping; no gesture library.
- Keep title, channel, views, reactions, comments/Q&A, and reporting immediately accessible.
- Expose an explicit mute/unmute control because browsers commonly block autoplay with sound.
- Pause all Shorts when the tab becomes hidden.
- Respect `prefers-reduced-motion` by disabling smooth programmatic scrolling.
- Preserve the existing server-side visibility query and 50-item cap.

## Acceptance criteria
1. The Shorts feed renders only videos already allowed by existing visibility rules.
2. Each Short is represented as a snap-aligned feed item with one vertical video surface.
3. Only the most-visible Short is automatically played; other videos are paused.
4. Keyboard navigation moves to the adjacent Short without breaking native controls.
5. Touch users can swipe/scroll naturally without a JavaScript gesture dependency.
6. Like/dislike, comments/Q&A, channel navigation, and report links remain available.
7. Empty-state and creator upload behavior remain intact.
8. No schema, migration, external API, cloud service, or paid dependency is introduced.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_immersive_feed
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope
- Infinite/AJAX pagination.
- Recommendation-algorithm changes.
- Pre-transcoding or adaptive bitrate streaming.
- Native-app gesture handling.
- Comment drawers/modals; existing detail-page comment/Q&A workflow remains authoritative.
