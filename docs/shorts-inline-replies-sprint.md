# Shorts Inline Replies Sprint

## Goal

Extend the immersive Shorts discussion experience so viewers can read and post replies to comments without leaving the Shorts feed.

## Scope

- Show up to two recent visible replies beneath each of the three recent top-level comments already shown in the Shorts feed.
- Show the visible reply count for each displayed comment.
- Let authenticated viewers post a reply from the Shorts feed.
- Return the viewer to the same Short after posting.
- Reuse the existing `Comment` parent relationship, validation form, moderation visibility, and notification services.
- Keep full discussion, editing/deletion, creator moderation, and Q&A on the existing video discussion surfaces.

## Acceptance criteria

- Hidden replies are never shown or included in displayed reply counts.
- Reply forms are available only to authenticated viewers.
- Replies can only be posted to visible top-level comments belonging to visible Shorts.
- A successful reply preserves the existing video-owner comment notification and parent-author reply notification behavior.
- Posting from the feed redirects to `/videos/shorts/#short-<video id>`.
- Standard-video comments, hidden comments, and replies-to-replies cannot be targeted through the Shorts reply endpoint.
- Existing Shorts autoplay, keyboard navigation, subscription, reactions, comment posting, reporting, and visibility behavior remains intact.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_inline_replies
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Architecture decisions

- Reuse the existing `Comment.parent` relationship rather than adding a Shorts-only discussion model.
- Prefetch visible replies with displayed comments to avoid per-comment database queries in the feed.
- Keep only a small reply preview in the immersive feed; the full discussion page remains the canonical complete thread view.
- Reuse `notify_comment()` and `notify_reply()` so notification semantics remain consistent across standard videos and Shorts.

## Out of scope

- Nested replies beyond one level.
- AJAX/live reply submission.
- Reply editing or deletion inside the Shorts feed.
- Q&A answer featuring inside the Shorts feed.
- Schema or migration changes.
- AWS, external APIs, paid services, workers, queues, or Terraform changes.
