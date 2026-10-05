# Comment Return Context Sprint

## Goal

Preserve the viewer's comment location after comment/reply mutations instead of always returning to the base video detail page.

## Scope

- Add safe same-host return-target handling for comment mutations.
- Preserve the current comment page/filter after posting a top-level comment or reply.
- Preserve the current full-thread route after posting a reply from that thread.
- Preserve the originating page/thread through comment edit and delete flows.
- Update cancel links in edit/delete confirmation pages to return to the originating location.
- Fall back to the canonical video detail route when no safe return target is supplied.
- Keep all existing visibility, ownership, moderation, and authentication rules unchanged.

## Acceptance criteria

1. Comment/reply POSTs honor a same-host relative return target.
2. External or malformed return targets are ignored.
3. Edit and delete preserve the originating comment page or thread through GET and POST.
4. Cancel links return to the originating location when safe.
5. Existing default redirects remain unchanged when no return target is supplied.
6. No schema, migration, dependency, worker, queue, AWS resource, paid service, or live-payment change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_comment_return_context video.test_comment_replies video.test_comment_pagination
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Expanding unlisted-share posting permissions
- AJAX/infinite scrolling
- Comment sorting changes
- Arbitrary nested replies
