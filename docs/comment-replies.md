# Threaded Comment Replies

## Delivered behavior

Add one-level comment conversations with privacy-safe rendering, creator moderation, author ownership, and deduplicated notifications.

## Delivered safeguards

- Authenticated viewers can reply to a visible top-level comment on a video they can view.
- Replies remain one level deep; reply routes reject reply-to-reply targets.
- Parent and reply must always belong to the same video.
- Video pages render visible replies beneath their visible parent in deterministic order.
- Hiding a parent hides the entire thread; hiding a reply hides only that reply.
- Reply authors retain existing edit and delete rights.
- Deleting a parent comment also deletes its replies after the existing confirmation.
- Creators can review and moderate replies through the existing queue.
- A reply notifies its parent author unless it is a self-reply.
- The video creator retains the existing new-comment notification without receiving a duplicate when they are also the parent author.
- Draft, trashed, hidden-parent, foreign-video, and forged reply requests fail safely.

## Architecture decisions

`Comment.parent` is a nullable self-reference with `CASCADE` deletion and a `replies` related name. Application validation restricts parents to top-level comments on the same visible video. Public rendering prefetches only visible direct replies for visible top-level comments.

Reply creation continues to use the existing comment notification for the video creator. A new reply notification targets the parent author and is suppressed for self-replies and when the parent author is the video creator, preventing duplicate inbox entries.

Migration `0012_comment_parent_notification_reply` will add the parent relationship and reply notification choice. No dependency, AWS resource, worker, paid service, or external messaging system is required.

## Local test plan

With Docker:

```bash
docker compose up --build --detach
docker compose ps
docker compose run --rm test
```

Without Docker:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Focused regression tests:

```bash
python manage.py test video.test_comment_replies
```

Coverage includes login and visibility, one-level enforcement, same-video integrity, deterministic rendering, parent/reply moderation, ownership reuse, cascade deletion, notification recipients and deduplication, invalid input, and migration drift.

The sprint-close non-Docker run passed Django checks, reported no migration drift, and completed all 174 tests. The 13 focused reply tests and adjacent comment suites pass. Compose configuration, both Docker shell scripts, and Python compilation validate. The complete containerized suite remains `docker compose run --rm test`.

Terraform is unaffected, so formatting and validation are not required. The repository-wide Terraform commands remain documented in the README.

## Out of scope

- Arbitrarily deep nesting
- Reply pagination and collapsing
- Mentions and notification preferences
- Real-time updates
- Rich text, attachments, reactions, and automated moderation
