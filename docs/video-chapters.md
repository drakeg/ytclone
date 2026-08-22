# Video Chapters

## Sprint contract

Authorized video owners and channel editors can define up to 50 ordered chapters
on upload or edit. Each nonblank line uses `MM:SS Title` or `HH:MM:SS Title`.
The first timestamp is `0:00`; later timestamps must increase strictly. Titles are
plain text and limited to 120 characters.

Viewers see chapters only when they can already view the associated video.
Chapter controls seek the native HTML video player and do not create a separate
visibility or sharing path.

## Local verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_chapters
python manage.py test
```

Docker Compose runs the same required checks:

```bash
docker compose run --build --rm test
```

No environment variable, dependency, AWS resource, paid service, or Terraform
change is planned.
