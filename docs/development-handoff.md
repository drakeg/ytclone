# Development Handoff

This document lets a new development session or assistant continue the project
without depending on prior chat history. Repository files and current GitHub
state are authoritative when they differ from this dated snapshot.

## Handoff snapshot — August 22, 2026

- Repository: `drakeg/ytclone`
- Default branch: `main`
- Latest merged work at handoff: [#104 — Add private video bookmarks](https://github.com/drakeg/ytclone/pull/104)
- Handoff documentation branch: `docs/chatgpt-handoff`
- Latest migration on that branch: `video/0023_video_bookmarks`
- Verified test count on that branch: 316

Before making changes, inspect GitHub rather than assuming this snapshot is still
current. Update local `main` and branch from it. Never reconstruct
already-completed work from this document.

## Product and architecture

VideoShare is a Django video-sharing application designed for low-cost local use
and an eventual AWS deployment. Django templates and small amounts of plain
JavaScript render the interface. SQLite is the local default; uploaded media is
stored locally unless private S3 media is explicitly enabled. Docker Compose is
the preferred reproducible application and test environment.

Important code locations:

- `video/models.py` — videos, channels, playlists, viewing data, notifications,
  team invitations, chapters, and bookmarks
- `video/views.py` plus focused `*_views.py` modules — request handling
- `video/services/` — business rules, authorization-sensitive operations, and
  query composition
- `video/templates/` and `video/static/` — server-rendered interface and browser behavior
- `monetization/` — sandbox and Stripe test-mode monetization
- `yt/settings.py` — environment-driven application configuration
- `compose.yaml` and `docker/` — local runtime and required test entrypoint
- `terraform/` — optional AWS media and budget infrastructure
- `docs/roadmap.md` — delivery process, completed sprints, deferred work, and candidates

Centralized visibility is security-sensitive. Use
`Video.objects.visible_to(user)` and the existing service-layer permission
helpers instead of duplicating visibility or ownership checks in new views.
Viewer history, progress, watch events, and bookmarks are private. Creator
analytics expose aggregates rather than viewer-level activity.

## Required delivery process

Every sprint follows this order:

1. Review the README, roadmap, affected feature documentation, architecture,
   AWS notes, Terraform, and current repository/PR state.
2. Put the sprint goal, scope, acceptance criteria, exclusions, architecture
   decisions, and both local test paths in the roadmap before implementation.
3. Commit that sprint-start documentation before application code.
4. Keep the implementation focused, put business logic in service modules, and
   add regression tests alongside behavior.
5. Keep Docker and non-Docker instructions accurate throughout the sprint.
6. Run the documented checks, update affected docs with delivered behavior and
   exact results, and make a separate sprint-close documentation commit.
7. Push a named branch and open a draft pull request. Do not merge without the
   repository owner's approval and local review.

A typical commit sequence is:

```text
docs: plan <feature> sprint
feat: add <feature>
docs: close <feature> sprint
```

Preserve unrelated user changes. Start from a clean, freshly updated branch and
never discard a dirty worktree to make it convenient.

## Start and test with Docker Compose

Create local configuration once:

```bash
cp .env.example .env
```

Replace the example `DJANGO_SECRET_KEY`, then start the application:

```bash
docker compose up --build --detach
docker compose ps
```

Open `http://localhost:8000/`. The root route redirects to `/videos/`. The web
entrypoint applies migrations automatically, and named volumes preserve SQLite
and uploaded media. If an old image reports a missing table, rebuild and confirm
migrations:

```bash
docker compose down
docker compose up --build --detach
docker compose exec web python manage.py showmigrations video
```

Run the complete required container verification with:

```bash
docker compose run --build --rm test
```

That service runs Django system checks, the migration-drift check, and the full
unit test suite. Stop the application without deleting local data using:

```bash
docker compose down
```

Do not add `--volumes` unless intentionally deleting the local database and
uploaded media.

## Test without Docker

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Add a focused test-module command for every sprint before the full suite. When a
change affects `terraform/` or its workflow, also run:

```bash
cd terraform/environments/dev
terraform fmt -check -recursive ../..
terraform init -backend=false
terraform validate
```

Terraform validation must not create resources and does not require AWS
credentials.

## Administrator access

Create an administrator in Docker:

```bash
docker compose exec web python manage.py createsuperuser
```

To promote an existing account, replace `your_username`:

```bash
docker compose exec -e DJANGO_ADMIN_USERNAME=your_username web python manage.py shell -c "from django.contrib.auth import get_user_model; user = get_user_model().objects.get(username=__import__('os').environ['DJANGO_ADMIN_USERNAME']); user.is_staff = True; user.is_superuser = True; user.save(update_fields=['is_staff', 'is_superuser']); print(f'Promoted {user.username} to administrator')"
```

## Recent schema sequence

- `0020_video_watch_events` — private watch-time telemetry and aggregate creator analytics
- `0021_team_invitation_notifications` — invitation notification linkage and activity
- `0022_video_chapters` — creator-managed player chapters
- `0023_video_bookmarks` — viewer-private labeled playback moments

Migration files are required source code. Any model change must include and test
its migration, and `video/test_migrations.py` must point to the current leaf.

## Choosing the next sprint

Pull request #104 was merged at handoff. Synchronize the repository and re-read
`docs/roadmap.md`; it is the authoritative backlog. Good low-cost candidates
already deferred in the documentation include:

- reliable orphaned local/S3 media cleanup with an auditable maintenance workflow
- optional channel-team invitation email delivery and scheduled reminders
- scheduled-upload notification delivery
- low-cost AWS application hosting and deployment when operating cost is justified

Select only one concern. Prefer a user-visible improvement that needs no paid
service unless the owner explicitly chooses infrastructure work. Record rejected
alternatives and out-of-scope work in the sprint plan so later sessions do not
silently expand scope.

## Suggested opening prompt for a new ChatGPT session

```text
Work with the drakeg/ytclone repository. First inspect current main, open pull
requests (especially #104), README.md, docs/development-handoff.md, and
docs/roadmap.md. Do not assume the handoff snapshot is current. Preserve existing
changes and follow the documented sprint process: sprint-start docs must be the
first commit, implementation and tests must stay focused, and sprint-close docs
must record exact Docker and non-Docker verification. Keep the application fully
testable with docker compose. Before coding, summarize repository state and
recommend one low-cost next sprint for approval.
```

Never paste `.env`, credentials, API keys, private media, database contents, or
other secrets into a chat. Share repository paths, command output, and redacted
configuration instead.
