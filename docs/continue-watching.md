# Continue Watching

## Sprint goal

Add private playback-position tracking so authenticated viewers can resume unfinished videos, while making the complete verification suite directly runnable in a Docker container.

## Planned behavior

- Authenticated playback periodically saves the current position and known duration.
- Returning to a video resumes from the viewer's saved position.
- The homepage shows unfinished videos in a Continue Watching section.
- Completed videos remain in watch history but do not appear in Continue Watching.
- Playback progress is private and scoped to the authenticated user.
- Anonymous playback continues to work without storing progress.

## Acceptance criteria

- The progress endpoint accepts authenticated POST requests only.
- Invalid JSON, non-numeric values, negative values, and positions beyond the duration are handled safely.
- Saved progress belongs only to the requesting user and video.
- Continue Watching contains unique unfinished videos ordered by most recently watched.
- A video at or near its known duration is excluded from Continue Watching.
- The video player resumes only the current user's saved position.
- Existing watch-history removal and clearing behavior remains intact.
- Contributors can run Django checks, migration-drift checks, and the full unit suite with one Docker Compose command.

## Architecture

Playback position and duration will extend the existing `WatchHistory` record so history and resume state retain the same user/video privacy boundary. A small authenticated Django endpoint will accept progress updates from the video player. Continue Watching queries will remain in the discovery service.

Docker Compose will gain a one-off test service backed by a shell script that runs the same Django verification sequence as CI. It will not start the development server, persist a test database, expose ports, or require AWS credentials.

## Test plan

Focused tests will cover endpoint authorization and validation, clamping, user isolation, resume context, completion filtering, ordering, and existing history behavior. Run the full suite without Docker:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Run the same suite in Docker:

```bash
docker compose run --rm test
```

Terraform checks are not applicable unless files under `terraform/` or its workflow change.

## Out of scope

- Cross-device real-time synchronization while two players are open
- Per-video chapters or bookmarks
- Playback analytics and creator reporting
- Recommendation ranking based on playback completion
- Background workers, caches, or external event pipelines
