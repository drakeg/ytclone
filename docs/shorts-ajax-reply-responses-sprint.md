# Shorts AJAX Reply Responses Sprint

## Goal
Establish a progressive-enhancement JSON contract for inline Shorts replies so the feed can add replies without reloading while retaining the existing HTML form fallback.

## Scope
- Return JSON after a valid AJAX reply submission.
- Include the saved reply ID, parent comment ID, author, text, and authoritative visible reply count.
- Return structured form validation errors for invalid AJAX submissions.
- Preserve the existing same-Short redirect for ordinary POST requests.
- Preserve existing visibility enforcement and top-level-parent-only reply rules.
- Preserve existing comment/reply notifications.
- Add explicit regression coverage rejecting replies to replies.

## Acceptance criteria
1. Valid AJAX reply submissions return HTTP 201 with server-confirmed reply data.
2. The response includes the authoritative visible reply count for the parent comment.
3. Invalid AJAX submissions return HTTP 400 with structured validation errors and create no reply.
4. Ordinary POST submissions retain the same-Short redirect fallback.
5. Replies to replies remain rejected.
6. Existing visibility, authentication, and notification behavior is unchanged.
7. No schema, migration, external API, cloud service, paid dependency, worker, queue, AWS resource, or Terraform change is introduced.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_ajax_reply_responses
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope
- JavaScript rendering of newly posted replies; that is the next focused sprint.
- Nested reply threads.
- Reply editing/deletion.
- Comment/reply ranking changes.
