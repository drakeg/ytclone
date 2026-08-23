# Orphaned Media Cleanup

## Sprint goal

Add a safe, auditable maintenance workflow that identifies uploaded media objects no longer referenced by application data and can explicitly remove sufficiently old orphaned objects from the configured Django media storage.

This sprint addresses the current lifecycle gap where permanent database deletion intentionally leaves uploaded files behind for later maintenance.

## Scope

The cleanup workflow manages only media paths owned by current application upload fields:

- `videos/files/`
- `videos/thumbnails/`
- `channels/thumbnails/`
- `categories/thumbnails/`

The command uses Django's configured default storage so the same implementation can inspect the local filesystem or private S3 media when that backend is explicitly configured.

## Acceptance criteria

- A management command reports referenced, orphaned, protected-recent, and deleted media without modifying storage by default.
- Existing database references from active **and trashed** videos, channels, and categories are always protected.
- Only known managed media prefixes are scanned; unrelated storage objects are ignored.
- Destructive cleanup requires an explicit `--delete` flag.
- Orphans newer than a configurable minimum age are protected from deletion to reduce races with uploads or database transactions.
- If storage cannot provide a trustworthy modification time, destructive mode skips that object rather than guessing it is safe.
- Nested storage paths are traversed recursively through Django's storage API.
- Deletion failures are reported and do not cause unrelated candidates to be silently treated as deleted.
- Core classification and cleanup logic lives in a service module; the management command is a thin interface.
- No request/view path automatically triggers cleanup.

## Architecture decisions

- Database rows remain the source of truth for whether a media name is referenced.
- Cleanup is intentionally decoupled from permanent video deletion; permanent deletion continues to remove database state first and leaves media reclamation to this auditable maintenance operation.
- Django's `default_storage` abstraction is used instead of directly importing filesystem or boto3 APIs.
- The default minimum age is 24 hours. Operators may increase it, but destructive cleanup rejects negative ages.
- Unknown-age objects can be reported as orphaned but are never deleted automatically.

## Delivered

- `cleanup_orphaned_media` management command with dry-run behavior by default.
- Explicit `--delete` destructive mode and configurable `--min-age-hours` safety window.
- Recursive scanning limited to the four managed media prefixes.
- Protection for every current database reference, including videos still retained in creator trash.
- Conservative handling of recent and unknown-age storage objects.
- Per-object deletion failure reporting.
- Storage-independent cleanup through Django's default storage abstraction, compatible with the existing local and private-S3 configuration.
- Service-layer classification and deletion logic in `video/services/media_cleanup.py`.
- Focused regression coverage for referenced media, trashed-video media, dry-run behavior, recent/unknown-age protection, unrelated prefixes, successful deletion, and deletion failures.
- AWS documentation updated to describe the operator-driven cleanup path.

## Operator usage

Dry run first:

```bash
python manage.py cleanup_orphaned_media
```

Delete eligible orphaned media only after reviewing the report:

```bash
python manage.py cleanup_orphaned_media --delete
```

Use a longer safety window when desired:

```bash
python manage.py cleanup_orphaned_media --delete --min-age-hours 72
```

The command is intentionally not scheduled automatically.

## Verification

Required focused and full commands remain:

```bash
python manage.py test video.test_media_cleanup
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
docker compose run --build --rm test
```

Verified on GitHub Actions against the PR merge ref:

- `python manage.py check` passed with no issues.
- `python manage.py makemigrations --check --dry-run` reported `No changes detected`.
- The full Django test suite passed: **322 tests**.

Local operator verification also exercised the real management command against the small development site, including the explicit destructive `--delete` path, without reporting an application failure.

No model migration, dependency, environment variable, paid service, AWS resource, or Terraform change was introduced.

## Deferred

- Automatic/scheduled cleanup and background workers.
- S3 lifecycle policies.
- Storage-size/billing reports and quotas.
- Automatic deletion coupled directly to HTTP video deletion.
- Cleanup outside the known application-managed upload prefixes.
