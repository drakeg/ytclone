# Shorts CSRF-aware AJAX recovery sprint

## Goal

Make the Shorts progressive-enhancement controllers surface the server's existing stale-CSRF recovery guidance instead of replacing a structured 403 response with a generic action failure.

## Scope

- Keep Django CSRF validation and the existing `video.security_views.csrf_failure` JSON contract unchanged.
- Teach Shorts comment/reply, reaction, and subscription controllers to recognize a 403 `{error: "csrf_failed", message: ...}` response.
- Show the server-provided recovery message in the existing inline status/error surface.
- Preserve typed comment/reply text on failure so a stale token does not discard user input.
- Preserve normal non-AJAX form fallback and existing controller ownership boundaries.
- Keep generic failure text for network errors, malformed responses, and unrelated HTTP failures.

## Acceptance criteria

- Stale-CSRF AJAX failures show the server's retry guidance.
- Comment and reply text is not cleared after a failed request.
- Reaction and subscription controls are re-enabled after failure.
- Successful AJAX behavior is unchanged.
- No CSRF exemptions, backend/schema/migration changes, dependencies, external APIs, cloud services, paid services, workers, queues, AWS resources, or Terraform changes.

## Verification

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_csrf_failure_recovery video.test_shorts_feed_controller
python manage.py test --parallel 4
docker compose run --build --rm test
```
