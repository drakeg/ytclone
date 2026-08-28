# CSRF Failure Recovery Fix

## Goal
Prevent stale or invalid CSRF tokens from exposing Django's technical 403 error page to normal users while preserving CSRF protection.

## Problem
Django rotates the CSRF token after authentication. A login form left open in a tab, restored with the browser Back button, or otherwise submitted after token rotation can fail with `CSRF token from POST incorrect`. With debug enabled, Django exposes a technical help page; with debug disabled it still returns a raw 403. This is a recoverable user-session condition and should have a normal application UX.

## Scope
- Configure a custom `CSRF_FAILURE_VIEW`.
- Keep Django CSRF validation fully enabled; do not exempt login or other POST endpoints.
- On stale login submissions, redirect to a freshly rendered login form.
- Preserve a safe same-origin `next` destination so login can still return the viewer to the protected page.
- On other stale form submissions, return to a safe same-origin referrer when available so a fresh token is rendered.
- Fall back to the video list when no safe referrer exists.
- Display a normal warning explaining that the form expired and should be retried.
- Reject external `next` and referrer URLs.

## Acceptance criteria
1. An invalid/stale CSRF token never renders Django's default CSRF failure page.
2. A stale login form redirects to a fresh login page instead of returning 403.
3. A safe protected-page `next` value survives recovery.
4. Other stale forms recover to their same-origin source page when possible.
5. External redirect targets are never accepted.
6. CSRF middleware and token validation remain enabled.
7. No schema, migration, external service, cloud, paid dependency, AWS resource, or Terraform change is introduced.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_csrf_failure_recovery
python manage.py test --parallel 4
docker compose run --build --rm test
```
