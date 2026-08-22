# ytclone

A Django-based video-sharing application being modernized into a secure, low-cost creator and viewer platform that runs locally with Docker and can later deploy to AWS through Terraform.

## Current capabilities

- Video uploads with configurable type and size validation
- Comments, mutually exclusive likes/dislikes, and subscriptions
- Session-based view counting
- Public user profiles and channels
- Public, unlisted, and private playlists
- Private watch history with remove and clear controls
- Grouped search across videos, channels, and visible playlists
- Video search sorting by relevance, date, views, and likes
- Homepage discovery for new, viewed, liked, recently watched, and public playlist content
- Private playback progress with Continue Watching and automatic resume
- Private creator analytics for uploads, views, reactions, and unique subscribers
- Private creator watch-time analytics with per-video duration, completion, and retention aggregates
- Private in-app notifications for comments, reactions, subscriptions, and channel-team invitations
- Explicit video-to-channel publishing with subscriber upload notifications
- Owner-only per-channel analytics with isolated lifetime metrics
- Owner-only video metadata editing, channel moves, and confirmed deletion
- Draft, immediate, and scheduled publishing with centralized visibility
- Creator-managed video chapters with accessible player seek controls
- Unlisted videos with hard-to-guess, revocable share links
- Private creator video library with publication-state filters and safe bulk visibility changes
- Recoverable creator video trash with 30-day retention and restore-to-draft safeguards
- Reversible creator comment moderation with owner-scoped bulk hide and restore
- Viewer-owned comment editing and confirmed deletion with moderation-safe behavior
- One-level threaded comment replies with parent-scoped moderation and deduplicated notifications
- Owner-managed, consent-based channel editor invitations for delegated uploads and video metadata changes
- Original responsive interface with accessible navigation, polished video surfaces, and shared creator components
- Self-service registration, profile management, and creator-channel onboarding
- Viewer and creator navigation tailored to each account's role
- Optional upload categories and thumbnails with drag-and-drop file selection
- Test-mode creator monetization with tips, channel memberships, refunds, and accounting
- Members-only video access with cancellation and payment-lifecycle handling
- Channel community posts, polls, and highlighted creator Q&A
- Optional private S3 media storage
- Terraform modules for private media storage and AWS budget alerts

## Local development with Docker

1. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

2. Replace `DJANGO_SECRET_KEY` in `.env` with a unique development value:

   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. Build and start the application in the background:

   ```bash
   docker compose up --build --detach
   ```

4. Confirm the web container is running and healthy:

   ```bash
   docker compose ps
   ```

5. Open `http://localhost:8000/`. The root route redirects to the application homepage at `/videos/`.

Follow application logs with:

```bash
docker compose logs --follow web
```

Press `Ctrl+C` to stop following logs; the background container continues running.

The container automatically applies database migrations and collects static files. SQLite data and uploaded media are stored in named Docker volumes so they survive container replacement.

Migration initialization is enforced by the image entrypoint, including when a custom web command is supplied. The complete migration package is version-controlled and verified by regression tests. If an older container is already running and reports a missing database table, rebuild it with:

```bash
docker compose down
docker compose up --build --detach
```

To initialize the database in a currently running container immediately, run:

```bash
docker compose exec web python manage.py migrate
```

The one-off `test` service is profile-isolated, so normal `docker compose up` starts only the application. Source files are bind-mounted for Django development reloads. Rebuild after changing Python dependencies or the Dockerfile:

```bash
docker compose up --build --detach
```

Create a new administrator account with:

```bash
docker compose exec web python manage.py createsuperuser
```

If your account already exists, promote it by replacing `your_username` below:

```bash
docker compose exec -e DJANGO_ADMIN_USERNAME=your_username web python manage.py shell -c "from django.contrib.auth import get_user_model; user = get_user_model().objects.get(username=__import__('os').environ['DJANGO_ADMIN_USERNAME']); user.is_staff = True; user.is_superuser = True; user.save(update_fields=['is_staff', 'is_superuser']); print(f'Promoted {user.username} to administrator')"
```

Then open `http://localhost:8000/admin/` and sign in with that account. If
`APP_PORT` is not `8000`, use the configured host port instead.

Stop the application with:

```bash
docker compose down
```

To also delete the local database and media volumes:

```bash
docker compose down --volumes
```

Volume deletion is irreversible. Use ordinary `docker compose down` when you want local data and uploaded media to remain available for the next startup.

## Local development without Docker

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1` instead.

## Administrator access

For a new administrator when running without Docker:

```bash
python manage.py createsuperuser
```

To promote an existing account on macOS or Linux, replace `your_username`:

```bash
DJANGO_ADMIN_USERNAME=your_username python manage.py shell -c "from django.contrib.auth import get_user_model; user = get_user_model().objects.get(username=__import__('os').environ['DJANGO_ADMIN_USERNAME']); user.is_staff = True; user.is_superuser = True; user.save(update_fields=['is_staff', 'is_superuser']); print(f'Promoted {user.username} to administrator')"
```

On Windows PowerShell:

```powershell
$env:DJANGO_ADMIN_USERNAME = "your_username"
python manage.py shell -c "from django.contrib.auth import get_user_model; user = get_user_model().objects.get(username=__import__('os').environ['DJANGO_ADMIN_USERNAME']); user.is_staff = True; user.is_superuser = True; user.save(update_fields=['is_staff', 'is_superuser']); print(f'Promoted {user.username} to administrator')"
```

Administrator access grants full Django administration privileges, including
the ability to change or delete application data. Grant it only to trusted
accounts.

## Run the full test suite locally

The Django checks below use the development settings from `.env`. Complete the setup steps for the environment you choose before running them.

### With Docker

After creating `.env`, run the same configuration, migration-drift, and unit-test checks used by CI with one command:

```bash
docker compose run --rm test
```

Compose builds the image automatically when needed. The one-off test container does not start the development server, expose a port, use the persistent development database, or require AWS credentials. Add `--build` after `run` to force an image rebuild after changing dependencies or the Dockerfile:

```bash
docker compose run --build --rm test
```

The test service runs `docker/test.sh`; keep that script aligned with the Django CI workflow whenever verification steps change.

### Without Docker

Activate the virtual environment and install dependencies as described above, then run:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

A successful migration-drift check prints `No changes detected`. If it reports model changes, create and review the required migration before closing the sprint.

### Terraform checks

Run Terraform checks when a change touches `terraform/` or the Terraform workflow. Terraform 1.13.5 matches CI.

```bash
cd terraform/environments/dev
terraform fmt -check -recursive ../..
terraform init -backend=false
terraform validate
```

These commands validate formatting and configuration without creating AWS resources. `terraform init` downloads the required providers; AWS credentials are not needed for formatting or validation.

## Media storage

Uploaded media uses the local filesystem by default and requires no AWS credentials.

Private S3 media storage can be enabled with:

```text
DJANGO_USE_S3_MEDIA=true
AWS_STORAGE_BUCKET_NAME=your-private-media-bucket
AWS_S3_REGION_NAME=us-east-1
```

The application uses the standard AWS SDK credential chain. Production deployments should use an IAM role rather than committed or long-lived access keys. See `docs/aws.md` for configuration and security notes.

## Deployment behavior

When `DJANGO_DEBUG=true`, the container starts Django's development server. With debug disabled, it starts Gunicorn. Production secrets and host values must be supplied through environment variables rather than committed files.

## Documentation

- `docs/roadmap.md` — completed work, current sprint status, delivery checklist, and next candidates
- `docs/unlisted-sharing.md` — revocable direct links and privacy boundaries
- `docs/publication-management.md` — creator filters, bulk visibility safeguards, and tests
- `docs/video-trash.md` — recovery, retention, permanent deletion, and media-cleanup boundaries
- `docs/comment-moderation.md` — reversible creator moderation, privacy, Compose workflow, and tests
- `docs/comment-ownership.md` — author editing, deletion, visibility boundaries, and tests
- `docs/comment-replies.md` — reply threads, moderation inheritance, notifications, and tests
- `docs/channel-teams.md` — editor permissions, owner safeguards, migration, and tests
- `docs/ui-design.md` — visual system, responsive behavior, accessibility, and verification
- `docs/viewer-creator-categories.md` — registration, role-aware onboarding, optional categories, and uploads
- `docs/monetization.md` — test-mode tips, memberships, Stripe configuration, accounting, and tests
- `docs/channel-community.md` — community posts, polls, highlighted Q&A, permissions, and tests
- `docs/post-expansion-hardening.md` — current correctness and privacy hardening scope
- `docs/publishing.md` — draft and scheduled visibility, privacy, and tests
- `docs/video-management.md` — owner-only editing, channel moves, deletion, and tests
- `docs/video-chapters.md` — timestamp syntax, permissions, player behavior, and tests
- `docs/channel-analytics.md` — owner-only channel metrics, privacy, and tests
- `docs/video-channels.md` — video channel ownership, migration, notifications, and tests
- `docs/notifications.md` — notification events, privacy, unread state, and tests
- `docs/creator-analytics.md` — creator metrics, privacy, architecture, and tests
- `docs/continue-watching.md` — playback progress, resume behavior, privacy, and tests
- `docs/discovery.md` — Homepage Discovery goals, behavior, architecture, and tests
- `docs/search.md` — Search and Discovery behavior and architecture
- `docs/security.md` — security guarantees and practices
- `docs/aws.md` — AWS media configuration
- `terraform/README.md` — Terraform usage and cost controls

## Current direction

The current sprint hardens the expanded onboarding, monetization, membership, and
community foundation. After it closes, the next sprint will be selected from the
roadmap using the same documentation-first process. Higher-cost AWS services will
be introduced only when usage justifies them.
