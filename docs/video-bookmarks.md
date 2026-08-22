# Private Video Bookmarks

## Sprint plan

Signed-in viewers will be able to save a short label with the current playback
position of any video they can view. Bookmarks remain private to their owner.
The video page will show that viewer's saved moments in timestamp order, while a
private bookmarks page will collect accessible saved moments across videos.

Saving the same position again will update the existing label. Bookmark creation
and removal will require POST requests, and all reads and writes will be scoped
to the authenticated user. If a video is deleted or is no longer visible to the
viewer, its bookmarks will not provide another way to access it.

The implementation will use Django models and ORM queries only. It introduces no
new dependency, environment variable, paid service, AWS resource, or Terraform
change.

## Local verification

Without Docker:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_bookmarks
python manage.py test
```

With Docker Compose, the test service runs Django checks, the migration-drift
check, and the full unit test suite:

```bash
docker compose run --build --rm test
```

These instructions must be updated with delivered behavior and the final test
results before the sprint closes.
