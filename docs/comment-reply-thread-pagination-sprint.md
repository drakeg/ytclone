# Comment Reply Thread Pagination Sprint

## Goal

Keep long comment threads usable by bounding replies on the video detail page while preserving access to the complete visible thread.

## Scope

- Show at most three visible replies beneath each top-level comment on the video detail page.
- Show the total visible reply count for each top-level comment.
- Add a dedicated full-thread route for a visible top-level comment.
- The full-thread view shows the parent comment and all visible replies in chronological order.
- Preserve existing author edit/delete controls, reporting controls, supporter badges, creator-highlighted Q&A answers, and reply submission.
- Preserve existing visibility, moderation, ownership, and one-level nesting rules.
- Keep the implementation server-rendered with no JavaScript dependency.

## Acceptance criteria

1. A top-level comment with more than three visible replies renders only the first three on the video detail page.
2. Hidden replies are excluded from both the preview count and the full thread.
3. A "View all replies" link appears only when additional visible replies exist.
4. The full-thread route rejects hidden parents, replies-as-parents, and comments on videos the viewer cannot access.
5. The full-thread view preserves existing reply actions and creator Q&A highlighting controls.
6. No schema, migration, dependency, worker, queue, AWS resource, paid service, or live-payment change is introduced.
7. Query behavior remains bounded and avoids per-comment reply queries.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_comment_replies
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Infinite scrolling or AJAX reply loading
- Arbitrary nested replies
- Mentions
- Real-time comments
- Rich text
- Changing top-level comment pagination
