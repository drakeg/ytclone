# AWS deployment notes

## Media storage modes

The application supports two media-storage modes:

- Local filesystem storage is the default and costs nothing beyond the application host disk.
- Private Amazon S3 storage is enabled with `DJANGO_USE_S3_MEDIA=true`.

Static assets continue to use Django's local static-files backend. This keeps the first deployment simple and avoids coupling application static files to the media bucket.

## S3 configuration

Required when S3 media storage is enabled:

```text
DJANGO_USE_S3_MEDIA=true
AWS_STORAGE_BUCKET_NAME=example-private-media-bucket
AWS_S3_REGION_NAME=us-east-1
```

Optional settings:

```text
AWS_S3_QUERYSTRING_EXPIRE=3600
AWS_S3_ENDPOINT_URL=
AWS_S3_CUSTOM_DOMAIN=
```

Uploaded objects are stored beneath the `media/` prefix. They remain private and generated URLs are signed. File overwriting is disabled so two uploads with the same filename do not replace one another.

## Credentials

Do not commit AWS access keys or place long-lived production credentials in `.env`.

The storage backend uses the standard boto3 credential chain. On AWS, the preferred approach is an IAM role attached to the application host. Local developers may use an AWS profile or temporary environment credentials outside the repository.

## Initial IAM scope

The application host should receive permissions only for its media bucket and objects. Terraform will define the final policy, but the expected operations are:

- list the media bucket
- read uploaded objects
- create uploaded objects
- delete uploaded objects through the explicit maintenance cleanup workflow

Public bucket access should remain blocked.

## Orphaned media cleanup

Permanent application deletion removes database state first and intentionally leaves media reclamation to an auditable maintenance operation. The same management command uses Django's configured storage backend for local media or private S3 media.

Always inspect a dry run first:

```bash
python manage.py cleanup_orphaned_media
```

The command scans only application-owned upload prefixes and protects all database-referenced objects, including media for videos still in recoverable trash. By default it also protects orphan candidates modified within the last 24 hours and any object whose modification time cannot be determined safely.

After reviewing the report, explicitly request destructive cleanup with:

```bash
python manage.py cleanup_orphaned_media --delete
```

Increase the safety window when appropriate, for example:

```bash
python manage.py cleanup_orphaned_media --delete --min-age-hours 72
```

Do not schedule destructive cleanup until the dry-run report and storage permissions have been verified in the target environment. S3 cleanup requires the application identity to have object-listing, modification-time metadata access, and deletion permissions for the configured private media prefix.

## Cost controls

S3 is disabled by default. Enabling it introduces usage-based storage, request, and data-transfer charges. Lifecycle policies and budget alerts will be added through Terraform before the production environment is provisioned.
