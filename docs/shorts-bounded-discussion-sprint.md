# Shorts bounded discussion sprint

## Goal
Keep the immersive Shorts feed responsive as comment threads grow by fetching only the discussion rows that the feed can actually render.

## Scope
- Preserve the existing 50-Short feed cap.
- Fetch at most the newest 3 visible top-level comments per Short.
- Fetch at most the newest 2 visible replies per rendered comment.
- Keep authoritative visible top-level comment and reply counts even when only recent rows are prefetched.
- Preserve existing ordering and all AJAX/non-JavaScript behavior.

## Acceptance criteria
- A Short with more than three comments renders only its newest three in the feed while showing the full visible comment count.
- A rendered comment with more than two replies renders only its newest two visible replies while showing the full visible reply count.
- Hidden replies do not contribute to the visible reply count or rendered recent replies.
- Existing Shorts interaction behavior remains unchanged.

## Verification
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test video.test_shorts_bounded_discussion`
- `python manage.py test --parallel 4`
- `docker compose run --build --rm test`

## Out of scope
- Pagination or a full discussion drawer.
- Schema or migration changes.
- New dependencies, external APIs, cloud services, AWS resources, paid services, workers, or queues.

## Next maintenance candidates
Continue the maintenance backlog from `docs/shorts-current-state.md`, with remaining inline Shorts JavaScript extraction as the next logical cleanup after this query-boundary work.
