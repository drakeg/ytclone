# Shorts AJAX Reply UI Sprint

## Goal
Progressively enhance inline Shorts reply forms so viewers can post replies without reloading the immersive feed or interrupting playback.

## Scope
- Load a dedicated reply enhancement script only on the Shorts feed.
- Intercept `.shorts-reply-form` submissions, including reply forms created dynamically after a new AJAX comment.
- Submit with the AJAX contract introduced in the prior sprint.
- Render only server-confirmed reply data using DOM APIs and `textContent`.
- Update the authoritative visible reply count.
- Keep at most the two most recent inline replies visible, matching the server-rendered feed behavior.
- Clear and close the reply form only after success.
- Preserve entered text and show an inline error on failure.
- Preserve the existing HTML form/CSRF/redirect fallback when JavaScript is unavailable.

## Acceptance criteria
1. Posting an inline reply does not reload the Shorts feed when JavaScript is available.
2. Playback and the current Short position remain unchanged.
3. Newly posted replies appear from server-confirmed JSON data.
4. Reply counts update from the authoritative server response.
5. Failed submissions retain the entered reply and expose an inline error.
6. Dynamically inserted comments from the AJAX comment sprint also receive no-reload reply behavior through delegated event handling.
7. The enhancement script loads only on the Shorts feed.
8. CSRF protection and ordinary POST fallback remain intact.
9. No schema, migration, external API, cloud service, paid dependency, worker, queue, AWS resource, or Terraform change is introduced.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_ajax_reply_ui
python manage.py test --parallel 4
docker compose run --build --rm test
```
