# Shorts Discussion Controller Sprint

## Goal

Finish decomposing social AJAX behavior out of the general Shorts feed controller by giving the existing discussion controller ownership of both top-level comments and replies.

## Scope

- Remove top-level comment rendering/submission from `shorts_feed.js`.
- Extend the already-loaded `shorts_reply_ajax.js` discussion controller to own top-level comments as well as replies.
- Preserve delegated reply handling so reply forms created after an AJAX comment continue to work.
- Preserve server-authoritative counts, CSRF form data, inline errors, safe DOM construction, and ordinary HTML form fallbacks.

## Acceptance criteria

- `shorts_feed.js` contains navigation/playback/sound/visibility behavior only and no social AJAX request code.
- Top-level comments post without reload and render only after a successful server response.
- Newly rendered comments include reply forms handled by the same discussion controller.
- Reply behavior remains unchanged.
- No backend, schema, migration, UI layout, dependency, external API, cloud, paid service, worker, queue, AWS, or Terraform changes.

## Verification

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_feed_controller video.test_shorts_ajax_comment_ui video.test_shorts_ajax_reply_ui
python manage.py test --parallel 4
node --check video/static/video/shorts_feed.js
node --check video/static/video/shorts_reply_ajax.js
docker compose run --build --rm test
```
