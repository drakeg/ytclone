# Shorts Sharing Controller Extraction Sprint

## Goal

Continue reducing the large inline Shorts feed controller by moving the self-contained sharing behavior into a namespaced static JavaScript controller without changing user-visible sharing behavior.

## Scope

- Add `video/static/video/shorts_share.js`.
- Load it only on the Shorts feed.
- Preserve Web Share API behavior when available.
- Preserve Clipboard API fallback and legacy `execCommand('copy')` fallback.
- Preserve transient `Copied`, `Copy failed`, and `Share failed` feedback.
- Preserve silent handling of user-cancelled native share dialogs.
- Capture the Share click before the existing inline fallback handler so only one sharing request runs.

## Acceptance criteria

- Sharing behavior remains unchanged for native-share-capable browsers.
- Clipboard and legacy copy fallbacks remain available.
- User cancellation does not show an error.
- The controller is namespaced under `video/` and loaded only on the Shorts feed.
- The existing inline handler remains available as a no-regression fallback during incremental extraction, but the new capture handler owns Share clicks.
- No schema, migration, backend, dependency, cloud, paid service, worker, queue, AWS, or Terraform changes.

## Verification

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_share_controller video.test_shorts_sharing
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope

- Removing the remaining inline Shorts feed controller in one large rewrite.
- Changing share URLs or adding social-network-specific share targets.
- Backend sharing APIs.
