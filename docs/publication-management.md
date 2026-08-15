# Creator Publication Management

## Sprint goal

Give creators one private place to review their videos by publication state and safely change the visibility of multiple owned videos.

## Scope and acceptance criteria

- Provide a login-protected creator video library containing only the current user's videos.
- Filter the library by all, draft, unlisted, scheduled, or published status.
- Keep ordering deterministic with newest uploads first.
- Allow POST-only bulk changes to draft, unlisted, or published.
- Restrict every bulk change to videos owned by the current user, even when forged IDs are submitted.
- Clear `publish_at` when a bulk action changes a video to draft, unlisted, or published.
- Treat invalid filters and actions safely without mutating videos.
- Keep scheduling as an individual edit because it requires a future publication time.
- Add a useful empty state and creator navigation.

Bulk publication changes will not send subscriber notifications. Notification delivery remains tied to a new upload that is published immediately; adding transition notifications requires explicit deduplication rules and is outside this sprint.

## Architecture decision

The management query and allowed bulk transitions remain explicit and owner-scoped. The view will never load submitted video IDs from the unrestricted video collection. Bulk updates use one owner-filtered queryset so a forged foreign ID cannot be changed.

No migration, dependency, environment variable, AWS resource, worker, or external service is required.

## Local test plan

With Docker:

```bash
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
python manage.py test video.test_publication_management
```

Coverage will include authentication, owner isolation, every status filter, invalid filters and actions, POST-only mutation, selected-video updates, foreign-ID protection, timestamp cleanup, and empty-state rendering.

Terraform is unaffected, so formatting and validation are not required for this sprint. The repository-wide Terraform commands remain documented in the README.

## Out of scope

- Bulk scheduling or timestamp editing
- Bulk channel, category, title, or description changes
- Subscriber notifications for publication-state transitions
- Select-all across pagination
- Background jobs, approval workflows, or channel teams
