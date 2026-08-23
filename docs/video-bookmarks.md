# Private Video Bookmarks

## Delivered behavior

Signed-in viewers can save a short label with the current playback position of a
video available through its normal visibility rules. Bookmarks remain private to
their owner. The video page shows that viewer's saved moments in timestamp order,
while a private Saved moments page collects accessible bookmarks across videos.

Saving the same rounded-second position again updates the existing label. Labels
are required, trimmed, and limited to 120 characters; positions are bounded from
zero through 24 hours. Bookmark creation and removal require POST requests, and
all reads and writes are scoped to the authenticated user. If a video is deleted
or is no longer visible to the viewer, its bookmarks will not provide another
way to access it.

The implementation uses Django models and ORM queries only. Migration
`0023_video_bookmarks` adds the private records, while validation and persistence
live in `video/services/bookmarks.py`. It introduces no
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

Django checks and migration-drift checks passed both directly and in Docker.
All 316 tests, including eight focused bookmark regressions, passed through both
local paths.
