# Comment Sort Toggle Sprint

## Goal

Let viewers choose whether top-level video comments are shown oldest-first or newest-first without changing the existing default behavior.

## Scope

- Add an Oldest / Newest sort control to video comments.
- Keep Oldest as the default to preserve current behavior.
- Apply sorting before pagination.
- Preserve the existing All / Questions filter when switching sort or paging.
- Reset to the first comment page when changing sort.
- Keep shared/unlisted video comment links on the current request path.
- Keep reply previews and full-thread reply ordering unchanged.
- Keep hidden-comment exclusion, moderation, Q&A, ownership, reporting, and return-context behavior unchanged.

## Acceptance criteria

1. Default comment ordering remains oldest-first.
2. `comments_sort=newest` reverses top-level comment ordering before pagination.
3. The Questions filter and selected sort work together.
4. Pager links preserve the active sort and filter.
5. Sort links preserve the active filter but intentionally reset pagination.
6. Invalid sort values fall back to Oldest.
7. Shared/unlisted routes remain on the shared request path.
8. No schema, migration, dependency, worker, queue, AWS resource, paid service, or live-payment change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_comment_sorting video.test_comment_pagination video.test_comment_replies video.test_comment_return_context
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Comment likes or ranking
- "Top comments" algorithms
- Reply sorting changes
- AJAX/infinite scrolling
- Real-time comments
