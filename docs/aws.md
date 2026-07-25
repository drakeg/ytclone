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
- delete uploaded objects when application deletion is implemented

Public bucket access should remain blocked.

## Cost controls

S3 is disabled by default. Enabling it introduces usage-based storage, request, and data-transfer charges. Lifecycle policies and budget alerts will be added through Terraform before the production environment is provisioned.
