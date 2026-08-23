# Orphaned Media Cleanup

## Sprint goal

Add a safe, auditable maintenance workflow that identifies uploaded media objects no longer referenced by application data and can explicitly remove sufficiently old orphaned objects from the configured Django media storage.

This sprint addresses the current lifecycle gap where permanent database deletion intentionally leaves uploaded files behind for later maintenance.

## Scope

The cleanup workflow will manage only media paths owned by current application upload fields:

- `videos/files/`
- `videos/thumbnails/`
- `channels/thumbnails/`
- `categories/thumbnails/`

The command will use Django's configured default storage so the same implementation can inspect the local filesystem or private S3 media when that backend is explicitly configured.

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
- The initial default minimum age is 24 hours. Operators may increase it, but destructive cleanup will reject negative ages.
- Unknown-age objects can be reported as orphaned but are never deleted automatically in this sprint.

## Out of scope

- Automatic scheduled cleanup or background workers
- S3 lifecycle policies or Terraform changes
- Deleting media during HTTP permanent-delete requests
- Reclaiming arbitrary objects outside the managed upload prefixes
- Storage-size billing reports
- Quotas, retention policies for active content, or automatic thumbnail regeneration
- Paid infrastructure or external cleanup services

## Verification

Focused verification:

```bash
python manage.py test video.test_media_cleanup
```

Complete non-Docker verification:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Complete Docker verification:

```bash
docker compose run --build --rm test
```

Useful operator dry run after implementation:

```bash
python manage.py cleanup_orphaned_media
```

Destructive cleanup will require explicit intent:

```bash
python manage.py cleanup_orphaned_media --delete
```
