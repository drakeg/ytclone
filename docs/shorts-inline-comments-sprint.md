# Shorts Inline Comments Sprint

## Goal
Keep lightweight viewer discussion inside the immersive Shorts feed.

## Scope
- Show the three newest visible top-level comments for each Short.
- Show a visible-comment count.
- Let authenticated viewers post a top-level comment directly from the feed.
- Return the viewer to the same Short after posting.
- Preserve the full video discussion page for replies, Q&A, editing, deletion, and moderation.
- Keep hidden comments out of the inline preview.

## Acceptance criteria
- Shorts display recent visible comments without exposing moderated/hidden comments.
- Authenticated viewers can submit a comment from the Shorts feed.
- Anonymous viewers receive a login path instead of a comment form.
- The Shorts-only comment endpoint refuses standard videos.
- Existing comment notifications continue to fire.
- No schema or migration changes are required.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_inline_comments
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Architecture decisions
- Reuse `Comment`, `CommentForm`, and `notify_comment` rather than introducing a Shorts-specific discussion model.
- Prefetch visible top-level comments with the feed query to avoid per-Short database lookups.
- Keep replies and Q&A on the full discussion surface for this focused slice.

## Out of scope
- Inline replies or Q&A.
- AJAX comment submission.
- Comment reactions.
- Ranking or recommendation changes.
- AWS, paid services, queues, workers, or Terraform changes.
