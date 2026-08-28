# Shorts AJAX Reactions Sprint

## Goal
Keep Like and Dislike interactions inside the immersive Shorts experience without reloading the page, while preserving normal form behavior when JavaScript is unavailable.

## Scope
- Enhance Shorts Like/Dislike forms with AJAX submission.
- Return current reaction state and counts as JSON for AJAX requests.
- Update Like/Dislike active styling, `aria-pressed`, and counts in place.
- Preserve mutual exclusion between Like and Dislike.
- Preserve existing creator reaction notifications.
- Disable the submitted reaction button while a request is running.
- Show a small inline error if the AJAX request fails.
- Preserve the existing redirect-to-same-Short path as a non-JavaScript fallback.

## Acceptance criteria
1. AJAX Like/Dislike requests return JSON rather than redirects.
2. The JSON payload includes `liked`, `disliked`, `like_count`, and `dislike_count`.
3. The feed updates both reaction buttons and counts without navigation or playback reset.
4. A failed AJAX request leaves the current feed state intact and shows an inline error.
5. A normal form POST still redirects back to the same Short.
6. Standard Shorts visibility and authentication requirements remain unchanged.
7. No schema, migration, external API, cloud service, paid dependency, worker, queue, AWS resource, or Terraform change is introduced.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_ajax_reactions
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope
- AJAX subscriptions.
- AJAX comments or replies.
- Optimistic updates before the server responds.
- Reaction analytics or ranking changes.
