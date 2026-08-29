# Shorts Reaction Serialization Sprint

## Goal
Prevent overlapping Like/Dislike requests for the same Short from racing each other and leaving the browser state inconsistent with the server.

## Scope
- Add a feed-scoped reaction handler loaded only on the Shorts feed.
- Serialize reaction requests per Short.
- Disable both Like and Dislike buttons for that Short while a request is in flight.
- Ignore duplicate submissions for the same Short until the active request finishes.
- Continue rendering only the server-confirmed reaction state and counts.
- Preserve the existing non-JavaScript form fallback and backend AJAX contract.
- Preserve independent reactions on different Shorts.

## Acceptance criteria
1. At most one reaction request per Short is active at a time.
2. Both reaction controls on that Short are disabled during the request.
3. A second submit event for the same Short is suppressed while the first request is active.
4. Controls are restored after either success or failure.
5. Server-returned liked/disliked state and counts remain authoritative.
6. Existing error feedback remains available.
7. No schema, migration, dependency, external service, cloud, AWS, paid-service, worker, queue, or Terraform change is introduced.

## Design
The handler is implemented in `video/static/shorts_reaction_ajax.js` rather than further expanding the already-large inline Shorts feed script. It attaches a capture-phase submit listener to the feed so it can own reaction submissions before the older form-level progressive-enhancement listener runs. A `WeakSet` tracks Shorts with an active request.

This is intentionally scoped per `.shorts-item`, not globally, so a viewer may still react to a different Short while another Short's reaction request is in flight.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_reaction_serialization video.test_shorts_ajax_reactions
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope
- Removing the legacy inline reaction helper from the large Shorts template.
- Extracting all remaining Shorts JavaScript.
- Changing reaction backend semantics.
- Optimistic reaction rendering.
