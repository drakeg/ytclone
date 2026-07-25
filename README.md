# ytclone

A Django-based video-sharing application inspired by YouTube. The project is being modernized into a secure, low-cost application that can run locally with Docker and later deploy to AWS through Terraform.

## Local development with Docker

1. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

2. Replace `DJANGO_SECRET_KEY` in `.env` with a unique development value. One option is:

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

Uploaded media uses the local filesystem by default. This remains the normal development mode and does not require AWS credentials.

Private S3 media storage can be enabled later with:

```text
DJANGO_USE_S3_MEDIA=true
AWS_STORAGE_BUCKET_NAME=your-private-media-bucket
AWS_S3_REGION_NAME=us-east-1
```

The application uses the standard AWS SDK credential chain. Production deployments should use an IAM role rather than committed or long-lived access keys. See `docs/aws.md` for the full configuration and security notes.

## Deployment behavior

When `DJANGO_DEBUG=true`, the container starts Django's development server. When debug mode is disabled, it starts Gunicorn. Production secrets and host values must be supplied through environment variables rather than committed files.

## Current roadmap

- Add minimal-cost Terraform infrastructure
- Add budget alerts and lifecycle policies
- Modernize the creator and viewer experience
- Introduce background media processing only when usage justifies it
