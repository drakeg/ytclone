# AJAX subscription response sprint

## Goal
Prepare channel subscriptions for in-place Shorts interaction by allowing the existing subscription endpoint to return authoritative JSON state for AJAX callers without changing its normal form behavior.

## Scope
- Detect AJAX subscription POSTs using `X-Requested-With`.
- Return the resulting subscribed state and current subscriber count as JSON.
- Preserve subscription notifications, self-subscription protection, channel availability enforcement, and normal safe redirects.
- Add focused regression coverage for subscribe, unsubscribe, fallback redirect, and self-subscription rejection.

## Acceptance criteria
- AJAX subscribe returns HTTP 200 with `subscribed: true` and the updated subscriber count.
- AJAX unsubscribe returns HTTP 200 with `subscribed: false` and the updated subscriber count.
- Ordinary form POSTs continue to honor safe `next` redirects.
- Existing authorization and notification behavior is unchanged.

## Test plan
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test video.test_ajax_subscriptions`
- `python manage.py test --parallel 4`

## Out of scope
- Changing the standard channel page UI.
- Schema or migration changes.
- External APIs, cloud services, workers, queues, paid dependencies, AWS resources, or Terraform changes.

## Next
Wire the Shorts subscribe control to this JSON response so subscribe/unsubscribe can update in place without resetting playback or feed position, while retaining the existing form as the non-JavaScript fallback.
