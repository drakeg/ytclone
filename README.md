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

3. Build and start the application:

   ```bash
   docker compose up --build
   ```

4. Open `http://localhost:8000`.

The container automatically applies database migrations and collects static files. SQLite data and uploaded media are stored in named Docker volumes so they survive container replacement.

Create an administrator account with:

```bash
docker compose exec web python manage.py createsuperuser
```

Stop the application with:

```bash
docker compose down
```

To also delete the local database and media volumes:

```bash
docker compose down --volumes
```

## Local development without Docker

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

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

- `docs/roadmap.md` — completed work, current sprint status, and next candidates
- `docs/search.md` — Search and Discovery behavior and architecture
- `docs/security.md` — security guarantees and practices
- `docs/aws.md` — AWS media configuration
- `terraform/README.md` — Terraform usage and cost controls

## Current direction

The next likely product sprint is a homepage discovery experience built from newest, popular, liked, recently watched, and public playlist sections. Background processing and higher-cost AWS services will be introduced only when usage justifies them.
