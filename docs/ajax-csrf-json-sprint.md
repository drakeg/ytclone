# AJAX CSRF JSON Recovery Sprint

## Goal

Return a structured JSON response for stale/invalid CSRF failures from AJAX requests while preserving the existing safe redirect recovery for normal browser forms.

## Scope

- Detect `XMLHttpRequest` submissions in the configured CSRF failure view.
- Return HTTP 403 with a stable `csrf_failed` error code and user-facing retry message.
- Do not redirect AJAX failures to HTML pages.
- Preserve login recovery, safe same-origin referer redirects, and external redirect rejection for ordinary form submissions.

## Acceptance criteria

- AJAX CSRF failures return JSON with status 403.
- The JSON response contains `error: csrf_failed` and the existing retry message.
- AJAX failures do not include a redirect `Location` header.
- Normal stale login forms continue to redirect to a fresh login page and preserve a safe `next` value.
- Other normal forms continue to return to a safe same-origin referer or the video list fallback.
- No schema, migration, dependency, UI, external service, cloud resource, paid service, worker, queue, AWS, or Terraform changes.

## Verification

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_csrf_failure_recovery
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope

- Automatic AJAX retry after obtaining a fresh CSRF token.
- Client-side copy changes for individual Shorts controls.
- Authentication/session behavior changes.
