# Shorts Static Namespace Sprint

## Goal
Keep Shorts-specific JavaScript under the Django app's `video/` static namespace so asset names cannot collide with similarly named files from other apps or future packages.

## Scope
- Move the Shorts reply AJAX script to `video/static/video/shorts_reply_ajax.js`.
- Move the Shorts reaction AJAX script to `video/static/video/shorts_reaction_ajax.js`.
- Update the base template to reference both namespaced assets.
- Update focused tests to read and assert the namespaced paths.
- Preserve the already-namespaced playback accessibility script.

## Acceptance criteria
- The Shorts feed loads all three Shorts helper scripts from the `video/` static namespace.
- Reply AJAX behavior is unchanged.
- Reaction serialization behavior is unchanged.
- Non-Shorts pages do not load the Shorts helper scripts.
- No duplicate unnamespaced reply/reaction assets remain.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_ajax_reply_ui video.test_shorts_reaction_serialization video.test_shorts_playback_accessibility
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope
- No JavaScript behavior changes.
- No template layout or visual changes.
- No model/schema/migration changes.
- No dependency changes.
- No external API, cloud service, AWS resource, Terraform, worker, queue, or paid-service changes.
