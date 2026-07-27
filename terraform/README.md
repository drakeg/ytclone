# Terraform

This directory contains the AWS infrastructure for ytclone. The initial scope is intentionally small and cost-conscious: a private S3 media bucket and an AWS monthly cost budget.

## Structure

```text
terraform/
├── environments/
│   └── dev/
└── modules/
    ├── budget/
    └── media-storage/
```

Every module keeps resource declarations, variables, and outputs in separate files.

## Before applying

1. Configure AWS credentials through an AWS profile, environment variables, or an instance role. Do not add access keys to Terraform files.
2. Copy the example values:

   ```bash
   cd terraform/environments/dev
   cp terraform.tfvars.example terraform.tfvars
   ```

3. Replace the example bucket name and notification email.
4. Initialize and review the plan:

   ```bash
   terraform init
   terraform fmt -check -recursive ../..
   terraform validate
   terraform plan
   ```

5. Apply only after reviewing every planned resource:

   ```bash
   terraform apply
   ```

## Cost behavior

- The budget defaults to $15 per month with actual-spend alerts at 80% and forecast alerts at 100%.
- S3 versioning is disabled by default because video versions can multiply storage costs.
- Incomplete multipart uploads are removed after seven days.
- The bucket blocks all public access and uses S3-managed encryption.
- This configuration creates no compute, load balancer, NAT Gateway, database, or CloudFront distribution.

AWS Budgets alerts are notifications, not hard spending limits. Costs may continue increasing after an alert.

## Application settings after apply

Use Terraform's bucket output with the Django configuration:

```text
DJANGO_USE_S3_MEDIA=true
AWS_STORAGE_BUCKET_NAME=<media_bucket_name output>
AWS_S3_REGION_NAME=us-east-1
```

The application should receive AWS permissions through an IAM role when compute is added. Static access keys should not be stored in `.env` files.
