# Shorts Reaction Controller Decomposition Sprint

## Goal

Remove the legacy reaction AJAX implementation from `shorts_feed.js` now that `video/shorts_reaction_ajax.js` is the authoritative reaction controller.

## Review context

The completed Shorts feed controller extraction moved the remaining inline feed JavaScript byte-for-byte into `video/static/video/shorts_feed.js`. That file still carries older reaction handling which is intentionally intercepted by the specialized serialized-reaction controller. Keeping both implementations increases maintenance risk and makes controller ownership unclear even though only the specialized controller should execute.

## Scope

- Remove reaction form discovery, state synchronization, request submission, and submit-listener registration from `shorts_feed.js`.
- Keep `video/shorts_reaction_ajax.js` as the sole JavaScript owner of Shorts Like/Dislike AJAX behavior.
- Preserve the standard HTML form fallback and all backend reaction contracts.
- Preserve feed navigation, playback, sound, subscriptions, comments, replies, sharing, and visibility behavior.
- Update focused controller tests and current-state documentation.

## Acceptance criteria

1. `shorts_feed.js` no longer references `data-short-reaction-form`, `submitReaction`, or `syncReaction`.
2. `video/shorts_reaction_ajax.js` remains loaded on the Shorts feed and retains per-Short request serialization.
3. Like/Dislike HTML forms remain in server-rendered markup for non-JavaScript fallback.
4. No subscription, comment, reply, sharing, playback, navigation, or sound behavior changes.
5. No backend, schema, migration, dependency, external service, cloud, paid service, worker, queue, AWS, or Terraform changes.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_feed_controller video.test_shorts_reaction_serialization video.test_shorts_ajax_reactions
python manage.py test --parallel 4
node --check video/static/video/shorts_feed.js
node --check video/static/video/shorts_reaction_ajax.js
docker compose run --build --rm test
```

## Out of scope

- Removing legacy sharing handling from `shorts_feed.js`; that is a separate focused slice.
- Subscription or comment controller extraction.
- CSS extraction or UI changes.
- Changes to reaction backend semantics.
