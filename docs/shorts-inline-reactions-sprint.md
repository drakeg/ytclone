# Shorts Inline Reactions Sprint

## Goal

Keep Like and Dislike interactions inside the immersive Shorts experience and clearly show the viewer's current reaction state.

## Scope

- Add Shorts-specific Like and Dislike POST endpoints.
- Preserve the existing mutual-exclusion behavior between Like and Dislike.
- Preserve existing creator reaction notifications.
- Return viewers to the same Short after toggling a reaction.
- Render active/inactive reaction state in the Shorts feed.
- Show both Like and Dislike counts in the feed.
- Reject standard videos at Shorts-specific reaction endpoints.

## Acceptance criteria

- Liking a Short does not navigate to the standard video detail page.
- Disliking a Short does not navigate to the standard video detail page.
- A viewer cannot simultaneously Like and Dislike the same Short.
- Toggling an active reaction removes it without creating another notification.
- Adding a new reaction creates the same creator notification used by the existing video reaction flow.
- The feed exposes the current viewer state with `aria-pressed` and active button styling.
- Standard videos return 404 from Shorts-specific reaction endpoints.
- Existing standard-video reaction routes remain unchanged.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_inline_reactions
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Architecture decisions

- Reuse the existing `Video.likes` and `Video.dislikes` relationships.
- Reuse `notify_reaction` and existing notification kinds.
- Keep standard-video reaction endpoints untouched to avoid changing established navigation outside Shorts.
- Use the already-prefetched reaction relationships to derive per-viewer state in the feed.

## Out of scope

- AJAX reaction toggles.
- New reaction types.
- Recommendation/ranking changes based on reactions.
- Schema or migration changes.
- AWS, paid services, workers, queues, or Terraform changes.
