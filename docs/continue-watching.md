# Continue Watching

## Delivered behavior

Authenticated viewers now retain private playback position and duration, can resume an unfinished video, and receive a Continue Watching homepage section. The complete verification suite is also directly runnable in a one-off Docker container.

## Playback and privacy

- Authenticated playback saves the current position and known duration about every ten seconds, when paused or completed, and when leaving the page.
- Returning to a video resumes from the viewer's saved position.
- The homepage shows unfinished videos in a Continue Watching section.
- Completed videos remain in watch history but do not appear in Continue Watching.
- Playback progress is private and scoped to the authenticated user.
- Anonymous playback continues to work without storing progress.

## Delivered safeguards

- The progress endpoint accepts authenticated POST requests only.
- Invalid JSON, non-numeric values, and invalid durations are rejected. Negative positions and positions beyond the duration are clamped safely.
- Saved progress belongs only to the requesting user and video.
- Continue Watching contains unique unfinished videos ordered by most recently watched.
- A video at or near its known duration is excluded from Continue Watching.
- The video player resumes only the current user's saved position.
- Existing watch-history removal and clearing behavior remains intact.
- Contributors can run Django checks, migration-drift checks, and the full unit suite with one Docker Compose command.

## Architecture

Playback position and duration extend the existing `WatchHistory` record so history and resume state retain the same user/video privacy boundary. The authenticated `playback_progress` endpoint accepts progress updates from the video player. Continue Watching queries remain in the discovery service.

Docker Compose includes a one-off `test` service backed by `docker/test.sh`, which runs the same Django verification sequence as CI. It does not start the development server, persist a test database, expose ports, or require AWS credentials.

## Test plan

`video/test_continue_watching.py` covers endpoint authorization and validation, clamping, user isolation, resume context, completion filtering, ordering, and homepage visibility. Existing watch-history tests continue to cover removal and clearing.

The sprint-close non-Docker run completed successfully with 63 tests. Django system checks passed and the migration-drift check reported no changes. The Compose file and test script passed static syntax validation. Docker execution was unavailable in the delivery environment because Docker was not installed; the containerized command below is designed for Docker Desktop or Docker Engine with Compose.

Run the full suite without Docker:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Run the same suite in Docker after copying `.env.example` to `.env`:

```bash
docker compose run --rm test
```

Terraform checks are not applicable unless files under `terraform/` or its workflow change.

## Migration and configuration

Migration `0005_watchhistory_playback_progress` adds non-negative position and duration fields with zero defaults. Existing history records remain valid and simply have no resumable progress until the viewer watches again. No new environment variables, dependencies, AWS resources, or paid services are required.

## Out of scope

- Cross-device real-time synchronization while two players are open
- Per-video chapters or bookmarks
- Playback analytics and creator reporting
- Recommendation ranking based on playback completion
- Background workers, caches, or external event pipelines
