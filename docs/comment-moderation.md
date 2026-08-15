# Creator Comment Moderation

## Sprint goal

Give creators a private review queue with reversible bulk comment moderation, and make the complete local application workflow reproducible with Docker Compose.

## Scope and acceptance criteria

- Provide a login-protected moderation page containing only comments on active videos owned by the current creator.
- Filter comments by all, visible, or hidden state.
- Order comments newest first with deterministic tie-breaking.
- Allow POST-only bulk hide and restore actions.
- Scope every mutation through creator-owned active videos so forged foreign comment IDs cannot be changed.
- Hide moderated comments from video detail pages without deleting their content or notifications.
- Treat invalid filters, actions, and IDs safely without mutation.
- Add creator navigation and a useful empty state.
- Make default `docker compose up --build` start the web application without launching the one-off test runner.
- Add a Compose health check and document detached startup, status, logs, administrator creation, tests, and shutdown.

## Architecture decisions

`Comment.is_hidden` provides reversible moderation without destructive deletion. Comment queries and bulk state changes live in a dedicated service and always traverse an active video owned by the authenticated creator. Existing comments remain visible after migration.

The Compose test service will use a profile so normal application startup runs only the long-lived web service. Explicit `docker compose run --rm test` remains the complete containerized Django check suite.

Migration `0011_comment_is_hidden` will add a backward-compatible boolean. No dependency, AWS resource, paid service, worker, or external moderation system is required.

## Local test plan

Bring up the application with Docker Compose:

```bash
cp .env.example .env
docker compose up --build --detach
docker compose ps
docker compose logs --follow web
```

Open `http://localhost:8000/videos/`. Create an administrator in another terminal with:

```bash
docker compose exec web python manage.py createsuperuser
```

Run the complete containerized suite with:

```bash
docker compose run --rm test
```

Stop the application without deleting its database or media volumes:

```bash
docker compose down
```

Without Docker:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Focused regression tests:

```bash
python manage.py test video.test_comment_moderation
```

Coverage will include authentication, ownership isolation, active-video scoping, filters, ordering, reversible bulk actions, foreign-ID protection, invalid input, public rendering, empty states, migration drift, and Compose configuration.

Terraform is unaffected, so formatting and validation are not required for this sprint. The repository-wide Terraform commands remain documented in the README.

## Out of scope

- Permanent bulk comment deletion
- Automated spam or toxicity classification
- Keyword blocklists
- Moderator roles and channel teams
- Appeals, audit logs, or external moderation services
