# Shorts AJAX Comment UI Sprint

## Goal
Complete progressive enhancement for top-level comments in the immersive Shorts feed so viewers can post without interrupting playback or losing feed position.

## Scope
- Mark the existing Shorts comment form for JavaScript enhancement.
- Submit comments with `fetch` using the JSON contract introduced in PR #138.
- Render only server-confirmed comment data.
- Update the authoritative visible comment count from the response.
- Remove the empty-state message after the first successful comment.
- Preserve CSRF protection and the existing HTML POST/redirect fallback.
- Disable the submit button while a request is in flight.
- Keep the entered comment when a request fails and expose a small inline error.
- Build inserted comment DOM with `textContent`, not HTML interpolation.

## Acceptance criteria
1. Posting a top-level Short comment does not reload the page when JavaScript is available.
2. Current playback and feed position remain unchanged.
3. New comment text and author come from the successful server response.
4. The visible comment count updates from the server response.
5. User-supplied comment content is never inserted with `innerHTML`.
6. Failed requests do not clear the textarea and expose an inline error.
7. The ordinary form action, CSRF token, and same-Short redirect remain usable without JavaScript.
8. Existing visibility, notification, moderation, reaction, subscription, sharing, and playback behavior remain unchanged.
9. No schema, migration, external service, paid dependency, worker, queue, AWS resource, or Terraform change is introduced.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_ajax_comment_ui
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope
- AJAX replies; those remain the next focused Shorts interaction slice.
- Comment editing/deletion.
- Changes to moderation or ranking.
