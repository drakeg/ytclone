# Shorts Inline Subscribe Sprint

## Goal

Let viewers subscribe or unsubscribe from a creator without leaving the immersive Shorts feed.

## Scope

- Show a Subscribe button beside the channel identity for authenticated viewers.
- Show Subscribed when the viewer already follows the channel.
- Never offer a creator a subscription control for their own channel.
- Return the viewer to the same Short after toggling subscription.
- Keep the existing channel-page subscription behavior unchanged when no return target is supplied.
- Validate return targets as same-host URLs to prevent open redirects.

## Acceptance criteria

- Anonymous viewers continue to see channel identity without a subscription form.
- Authenticated non-owners see Subscribe or Subscribed based on current state.
- Toggling from Shorts updates the existing Channel.subscribers relationship and returns to `/videos/shorts/#short-<id>`.
- Existing notification behavior remains intact when a new subscription is created.
- External return URLs are rejected in favor of the channel detail fallback.
- Existing Shorts visibility, autoplay, navigation, reactions, reporting, and comments/Q&A behavior is unchanged.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_inline_subscribe
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Architecture decisions

- Reuse the existing `Channel.subscribers` many-to-many relationship and `subscribe` endpoint.
- Compute the viewer's subscribed channel IDs once for the feed rather than issuing a subscription query per Short.
- Use a validated POST `next` value so the general subscription endpoint can preserve origin without creating a Shorts-only mutation endpoint.

## Out of scope

- AJAX subscription toggles.
- Notification preference controls.
- Recommendation/ranking changes based on subscription state.
- Schema or migration changes.
- AWS, paid services, workers, queues, or Terraform changes.
