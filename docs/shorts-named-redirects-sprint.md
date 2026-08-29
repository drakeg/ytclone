# Named Shorts Redirects Cleanup

## Goal
Remove hardcoded Shorts feed paths from non-JavaScript fallback redirects so route changes cannot silently break Like, Dislike, Comment, or Reply flows.

## Scope
- Introduce one helper that builds a Short anchor from Django's named `shorts_feed` route.
- Use it for Like, Dislike, Comment, and Reply fallback redirects.
- Preserve all AJAX JSON responses and existing behavior.
- Add focused behavior tests for all four fallback redirects.

## Acceptance criteria
1. No affected fallback redirect embeds `/videos/shorts/` directly.
2. Like and Dislike fallback POSTs return to the same Short via `reverse("shorts_feed")`.
3. Comment and Reply fallback POSTs return to the same Short via `reverse("shorts_feed")`.
4. AJAX behavior remains unchanged.
5. No schema, migration, UI, external API, cloud service, paid dependency, AWS resource, or Terraform change is introduced.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_named_redirects
python manage.py test --parallel 4
docker compose run --build --rm test
```
