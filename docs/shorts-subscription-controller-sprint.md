# Shorts Subscription Controller Sprint

## Goal

Make the subscription interaction a focused Shorts controller instead of a responsibility of the general feed controller.

## Scope

- Add `video/static/video/shorts_subscription_ajax.js` as the sole JavaScript owner of subscribe/unsubscribe progressive enhancement.
- Preserve the existing AJAX request headers and server-authoritative `subscribed` response handling.
- Preserve the server-rendered POST form, CSRF token, and safe `next` redirect fallback.
- Remove subscription code from `video/static/video/shorts_feed.js`.
- Keep the controller loaded only on the Shorts feed route.

## Acceptance criteria

- Subscribe/unsubscribe continues without a page reload when JavaScript is available.
- The button label, `aria-pressed` state, and Bootstrap classes are updated from the server response.
- Failed requests restore the button and display the existing inline error.
- The ordinary HTML form remains functional without JavaScript.
- `shorts_feed.js` contains no subscription form selector, subscription submit helper, or subscription state helper.
- No backend, schema, migration, dependency, external service, cloud, paid service, worker, queue, AWS, or Terraform change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_ajax_subscriptions video.test_ajax_subscriptions video.test_shorts_feed_controller
python manage.py test --parallel 4
node --check video/static/video/shorts_feed.js
node --check video/static/video/shorts_subscription_ajax.js
docker compose run --build --rm test
```

## Out of scope

- Top-level comment controller extraction.
- CSRF-specific user guidance in AJAX clients.
- CSS extraction or visual changes.
