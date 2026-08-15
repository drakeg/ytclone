# Creator Video Trash and Restore

## Delivered behavior

Replace immediate destructive video deletion with an owner-only trash, a 30-day recovery window, safe draft restoration, and explicit permanent deletion after retention.

## Delivered safeguards

- Moving a video to trash is POST-only and owner-only.
- Trashed videos disappear from detail pages, discovery, search, channels, categories, profiles, playlists, history, and creator publication management.
- Related comments, reactions, history, playlist entries, and notifications remain intact during retention.
- Creators can review only their own trashed videos in a private trash view.
- Restore is POST-only, owner-only, and returns a video as a draft with no scheduled publication time.
- Permanent deletion is owner-only, requires confirmation and POST, and is unavailable until 30 days after deletion.
- Permanent deletion removes the database record and related database records through existing relationships.
- Invalid, foreign, active, and too-recent permanent-deletion requests fail safely.
- Existing videos remain active after migration.

## Architecture decisions

`Video.deleted_at` records soft deletion. The centralized visibility policy excludes every trashed video, including for its owner, while dedicated owner-scoped trash queries provide recovery access. A single retention constant defines the 30-day boundary used by both the interface and mutation checks.

Trashing and restoring do not delete or rewrite uploaded media. Permanent database deletion also leaves storage objects in place for this sprint because database and local/S3 storage operations are not transactional together. Reliable orphan-media cleanup requires an auditable maintenance workflow and is deliberately deferred.

Migration `0010_video_deleted_at` adds a nullable timestamp and leaves every existing video active. No dependency, environment variable, AWS resource, worker, or external service is required.

## Local test plan

With Docker:

```bash
docker compose run --rm test
```

Without Docker:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Focused regression tests:

```bash
python manage.py test video.test_video_trash
```

Coverage includes authentication, ownership, soft deletion, public-surface exclusion, retained relationships, private trash isolation, draft restoration, retention boundaries, permanent deletion, media preservation, and migration drift.

The sprint-close non-Docker run passed Django checks, reported no migration drift, and completed all 134 tests. The 11 focused trash tests also pass. Docker Compose configuration, `docker/test.sh` syntax, and Python compilation validate, but the Docker daemon was unavailable on the delivery host; run `docker compose run --rm test` on a Docker-enabled machine.

Terraform is unaffected, so formatting and validation are not required for this sprint. The repository-wide Terraform commands remain documented in the README.

## Out of scope

- Automatic purge jobs
- Local or S3 media-object deletion
- Administrative retention overrides
- Bulk trash, restore, or purge actions
- Restoring the previous publication state
