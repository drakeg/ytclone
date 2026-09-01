# Shorts Feed Controller Extraction Sprint

## Goal

Move the remaining executable Shorts feed JavaScript out of the Django template
and into the app's static namespace without changing user-visible behavior.

## Review context

Work merged through PR #157 introduced the Shorts format, local clip generation,
the immersive feed, progressive AJAX interactions, and focused static controllers
for replies, serialized reactions, playback accessibility, and sharing. The main
feed controller still remains as one minified inline script in
`video/templates/videos/shorts_feed.html`. This makes the template harder to
review, keeps behavior outside the established static namespace, and complicates
independent browser-controller testing.

## Scope

- Move the existing controller to `video/static/video/shorts_feed.js`.
- Load it only for the named `shorts_feed` route.
- Preserve feed activation, IntersectionObserver behavior, scroll/keyboard
  navigation, autoplay, visibility pausing, sound preference, and play/mute controls.
- Preserve existing subscription, reaction, top-level comment, and sharing
  progressive enhancement while the focused controllers continue intercepting
  the interactions they already own.
- Preserve non-JavaScript HTML form behavior and every backend contract.
- Add focused source and rendered-template regression coverage.

## Acceptance criteria

1. The Shorts template has no inline executable `<script>` block.
2. The namespaced controller is present on the Shorts feed and absent elsewhere.
3. Controller initialization remains guarded when no feed element exists.
4. Existing IntersectionObserver, keyboard, playback, sound, visibility,
   subscription, reaction, comment, and sharing behavior remains represented.
5. Existing specialized controllers remain loaded and prevent duplicate owned actions.
6. No schema, migration, backend, dependency, cloud, paid-service, worker, queue,
   AWS, or Terraform change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_feed_controller
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope

- Rewriting or modularizing the controller's behavior during the move
- Removing the focused reply, reaction, playback-accessibility, or sharing controllers
- Styling or markup redesign
- CSS extraction
- Backend response or authorization changes
- Database, infrastructure, or paid-service changes
