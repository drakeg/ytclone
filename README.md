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

## Deployment behavior

When `DJANGO_DEBUG=true`, the container starts Django's development server. When debug mode is disabled, it starts Gunicorn. Production secrets and host values must be supplied through environment variables rather than committed files.

## Current roadmap

- Stabilize authentication, authorization, and video interactions
- Add automated tests for core application behavior
- Add AWS-ready media storage
- Add minimal-cost Terraform infrastructure
- Modernize the creator and viewer experience
