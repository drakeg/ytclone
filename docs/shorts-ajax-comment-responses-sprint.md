# Shorts AJAX Comment Responses Sprint

## Goal
Add a server-side JSON contract for posting top-level comments from the immersive Shorts feed, while preserving the existing HTML form redirect behavior as a non-JavaScript fallback.

## Scope
- Detect AJAX requests using the existing Shorts request convention.
- Return the saved comment ID, author, text, reply URL, and authoritative visible top-level comment count after successful creation.
- Return structured form validation errors with HTTP 400 for invalid AJAX submissions.
- Preserve the existing creator notification behavior.
- Preserve visibility enforcement and rejection of standard videos.
- Preserve the existing redirect back to the same Short for ordinary POSTs.

## Acceptance criteria
1. A valid AJAX comment POST returns HTTP 201 and the saved comment payload.
2. The returned count reflects visible top-level comments for the Short.
3. Invalid AJAX input returns HTTP 400 and does not create a comment.
4. Creator notifications are unchanged.
5. Standard videos remain invalid for the Shorts comment endpoint.
6. Normal form POSTs still redirect to the same Short anchor.
7. No schema, migration, external API, cloud service, paid dependency, worker, queue, AWS resource, or Terraform change is introduced.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_ajax_comment_responses
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope
- JavaScript wiring of the existing Shorts comment form; that is the next focused sprint.
- AJAX replies.
- Comment editing/deletion or moderation changes.
- Comment ranking or pagination changes.
