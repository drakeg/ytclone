# Channel Directory Search and Pagination Sprint

## Goal

Keep the public Channels directory useful as the creator community grows by adding bounded search and pagination without changing channel moderation visibility.

## Scope

- Search available channels by channel name, description, or owner username.
- Trim surrounding whitespace and cap the search term at 120 characters.
- Apply the existing suspended-channel visibility boundary before search.
- Preserve the existing ordering: subscriber count descending, then channel name, then primary key.
- Paginate the filtered directory at 24 channels per page.
- Preserve the active search query in pager links.
- Reset pagination when a new search is submitted.
- Keep existing subscriber/public-video count annotations and channel card behavior.

## Acceptance criteria

1. Channel directory renders at most 24 channels per page.
2. Search matches channel name, description, and owner username case-insensitively.
3. Search is applied before pagination.
4. Blank/whitespace-only search behaves like no search.
5. Pager links preserve the active search query.
6. Search submission resets the page.
7. Non-staff users cannot reveal suspended channels through search.
8. Staff retain the existing ability to inspect suspended channels.
9. Subscriber/public-video counts and popularity ordering remain correct.
10. No schema, migration, dependency, worker, queue, AWS resource, paid service, or live-payment change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_channel_directory
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Channel sorting controls
- Fuzzy/full-text search
- Search ranking changes
- Category/tag filters
- Subscription recommendations
- Background indexing
