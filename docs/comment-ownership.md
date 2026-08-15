# Viewer Comment Ownership

## Delivered behavior

Let authenticated viewers correct or remove their own comments without weakening creator moderation, video visibility, or ownership boundaries.

## Delivered safeguards

- Comment authors can edit only their own comments on active videos they can currently view.
- Editing changes only comment text and never changes creator moderation state.
- A hidden comment remains hidden after its author edits it.
- Comment authors can permanently delete only their own comments after an explicit confirmation and POST.
- Other viewers and video creators cannot use author routes unless they wrote the comment.
- Comments on trashed or otherwise inaccessible videos cannot be edited or deleted through direct URLs.
- Empty edits are rejected with useful form feedback.
- Owner controls appear beside the author's visible comments without exposing controls to other viewers.
- Existing creator hide/restore behavior remains unchanged.

## Architecture decisions

The existing `CommentForm` remains the single comment-text validator. Author mutation views resolve comments through both `author=request.user` and the centralized active-video visibility policy. Editing uses the existing record, preserving `is_hidden`; deletion uses an explicit confirmation page and POST mutation.

Comment deletion remains permanent because it is an individual action initiated by the comment author, not a bulk moderation action. Existing video notifications target the video rather than the comment record and remain available after comment deletion.

No migration, dependency, environment variable, AWS resource, worker, or external service is required.

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
python manage.py test video.test_comment_ownership
```

Coverage includes authentication, author isolation, creator/non-author rejection, form validation, hidden-state preservation, confirmation and POST requirements, inaccessible-video rejection, rendering controls, deletion, and existing moderation compatibility.

The sprint-close non-Docker run passed Django checks, reported no migration drift, and completed all 161 tests. The 11 focused comment-ownership tests also pass. Compose configuration, both Docker shell scripts, and Python compilation validate. Local Compose application startup was confirmed after the merged migration-baseline hotfix; the complete containerized suite remains `docker compose run --rm test`.

Terraform is unaffected, so formatting and validation are not required for this sprint. The repository-wide Terraform commands remain documented in the README.

## Out of scope

- Comment version history or undo
- Soft deletion and recovery for viewer comments
- Editing comments on inaccessible videos
- Replies, threads, mentions, or rich text
- Creator editing of viewer-authored comments
