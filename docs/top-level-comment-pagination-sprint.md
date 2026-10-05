# Top-Level Comment Pagination Sprint

## Goal

Bound top-level comment rendering on video detail pages so large conversations remain usable and query work scales predictably.

## Scope

- Paginate visible top-level comments at 10 per page.
- Apply the existing All / Questions filter at the queryset layer before pagination.
- Keep the existing three-reply preview and full-thread behavior unchanged.
- Preserve hidden-comment exclusion, reply counts, moderation, Q&A, ownership, reporting, and supporter badges.
- Use the current request path for comment filter and pager links so valid unlisted shared-video routes stay on their share URL.
- Keep pagination server-rendered and dependency-free.

## Acceptance criteria

1. Video detail renders at most 10 visible top-level comments per page.
2. Hidden top-level comments do not affect page counts.
3. The Questions filter paginates only question comments rather than filtering after pagination.
4. Invalid/out-of-range page values fall back safely through Django's paginator behavior.
5. Pager links preserve the active comment filter.
6. Shared/unlisted video comment pagination remains on the shared route.
7. Existing bounded reply previews remain limited to three visible replies per top-level comment.
8. No schema, migration, dependency, worker, queue, AWS resource, paid service, or live-payment change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_comment_pagination video.test_comment_replies
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- AJAX/infinite scrolling
- Changing comment sort order
- Arbitrary nested replies
- Mentions or real-time updates
- Rich text
