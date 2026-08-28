# Shorts AJAX Subscriptions Sprint

## Goal
Complete progressive-enhancement support for channel subscriptions in the immersive Shorts feed so viewers can subscribe or unsubscribe without interrupting playback or losing feed position.

## Scope
- Mark Shorts subscription forms for JavaScript enhancement.
- Submit subscription changes with `fetch` using the AJAX contract introduced in the preceding sprint.
- Update Subscribe/Subscribed text, visual state, and `aria-pressed` from the server response.
- Disable the button while a request is in flight to avoid duplicate toggles.
- Show a small inline error when the request fails.
- Preserve the existing HTML form action, CSRF token, and safe `next` redirect as the no-JavaScript fallback.

## Acceptance criteria
1. Subscribing or unsubscribing from the Shorts feed does not reload the page when JavaScript is available.
2. Playback and current feed position are preserved during a successful subscription change.
3. The button state is derived from the authoritative server JSON response rather than optimistic client mutation.
4. Failed requests leave the existing subscription state intact and expose an inline error.
5. The form continues to work without JavaScript and returns to the same Short.
6. Existing channel availability, self-subscription prevention, notification behavior, and authorization remain unchanged.
7. No schema, migration, external API, cloud service, paid dependency, worker, queue, AWS resource, or Terraform change is introduced.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_ajax_subscriptions
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope
- Changing subscription semantics outside the Shorts feed.
- Persisting UI state independently of the server.
- Subscriber analytics or recommendation changes.
- AJAX comments/replies; those remain a later focused sprint.
