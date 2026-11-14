# Local Docker LAN Reliability Sprint

## Goal

Make a fresh Docker checkout start reliably and support explicit LAN access without machine-specific repository edits.

## Observed failures

A clean local checkout on macOS exposed two reproducible setup problems:

1. The fresh `sqlite_data` named volume mounted at `/app/data` was root-owned, while the image runs as the unprivileged `app` user, causing `sqlite3.OperationalError: unable to open database file`.
2. `compose.yaml` hard-coded `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`, so values in `.env` could not enable another LAN hostname/IP.

## Scope

- Create and chown `/app/data` in the image before switching to the `app` user so a fresh named SQLite volume inherits the intended ownership.
- Let the web service use `.env`-provided `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`, with safe localhost defaults.
- Preserve the existing configurable `APP_PORT` behavior.
- Document LAN access using an explicit local IP/hostname and trusted origin.
- Keep local development HTTP-only/debug behavior unchanged.
- Update stale runtime documentation to Django 6.1.3, Stripe 17.0.0, and Terraform 1.17.2.
- Add source-level regression coverage for Dockerfile/Compose invariants.

## Acceptance criteria

1. Dockerfile creates `/app/data`, `/app/media`, and `/app/staticfiles` before `USER app` and chowns them to `app:app`.
2. Compose web `DJANGO_ALLOWED_HOSTS` defaults to localhost/loopback/web but can be overridden through `.env`.
3. Compose web `DJANGO_CSRF_TRUSTED_ORIGINS` defaults to localhost at the selected `APP_PORT` but can be overridden through `.env`.
4. README explains how to add a LAN IP/hostname and origin without committing secrets or machine-specific values.
5. Runtime docs match current requirements/Terraform CI.
6. Existing test service isolation and application security settings remain unchanged.
7. No schema, migration, paid service, AWS resource, worker, queue, or live-payment change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_local_docker_runtime
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

Manual clean-start verification:

```bash
docker compose down --volumes
docker compose up --build --detach
docker compose ps
```

LAN verification is performed by setting the machine's LAN address in `.env` and confirming the configured URL responds from the host/LAN.

## Out of scope

- HTTPS/TLS
- Reverse proxies
- Automatic network-interface discovery
- Production deployment changes
- Changing the default port
- New Docker services
