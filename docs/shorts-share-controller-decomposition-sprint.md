# Shorts Share Controller Decomposition Sprint

## Goal

Make `video/static/video/shorts_share.js` the sole JavaScript owner of Shorts sharing behavior by removing the shadowed sharing implementation from the general feed controller.

## Scope

- Remove the `data-short-share` collection from `shorts_feed.js`.
- Remove the legacy Web Share and clipboard helper functions from `shorts_feed.js`.
- Remove the legacy per-button share listeners from `shorts_feed.js`.
- Preserve `shorts_share.js` as the active capture-phase sharing controller.
- Preserve server-rendered Share markup and all current user-visible behavior.
- Update controller ownership regression tests and the current-state handoff.

## Acceptance criteria

- `shorts_feed.js` contains no sharing-specific implementation.
- `shorts_share.js` continues to contain the Web Share, clipboard, and fallback-copy paths.
- Sharing remains available from the Shorts feed.
- Feed navigation, playback, sound, subscriptions, comments, replies, reactions, and visibility lifecycle remain unchanged.
- No backend, schema, migration, dependency, cloud, paid-service, worker, queue, AWS, or Terraform changes.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_feed_controller video.test_shorts_share_controller video.test_shorts_sharing
python manage.py test --parallel 4
node --check video/static/video/shorts_feed.js
node --check video/static/video/shorts_share.js
docker compose run --build --rm test
```

## Out of scope

- Extracting subscription or top-level comment enhancement.
- Static CSS extraction.
- Changing sharing UX or adding new sharing providers.
