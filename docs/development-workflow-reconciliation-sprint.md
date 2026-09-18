# Development Workflow Reconciliation Sprint

## Goal

Restore a trustworthy contributor handoff after the feature work merged through
PR #201 by reconciling top-level documentation, local test prerequisites, and
dependency-update automation with the current repository.

## Scope

- Update the README, roadmap, and development handoff for capabilities merged
  since the Shorts feed controller extraction.
- Document reproducible Docker and non-Docker verification, including the
  FFmpeg capabilities required by the real Shorts rendering smoke test.
- Make the smoke test skip cleanly when an installed FFmpeg binary does not
  provide the required filters or encoders.
- Correct the Terraform Dependabot manifest location.
- Align Renovate's Django release policy with the supported Django requirement.
- Add focused regression coverage for FFmpeg capability detection.

## Acceptance criteria

1. The README describes the current viewer, discovery, upload, and notification
   capabilities delivered through PR #201.
2. The roadmap and development handoff identify the current migration leaf,
   test count, architecture boundaries, and sensible next sprint candidates.
3. Contributors can distinguish an unavailable or incompatible FFmpeg binary
   from an application failure when running tests without Docker.
4. Docker remains the guaranteed environment for the real FFmpeg smoke test.
5. Dependabot searches the directory containing the Terraform configuration.
6. Renovate no longer applies a Django 5.2-only policy to a Django 6.1 project.
7. Django checks, migration-drift checks, focused tests, the full unit suite,
   and Terraform validation pass. The Docker suite is run when the daemon is
   available, and any environmental limitation is recorded before closure.

## Local verification

Without Docker:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_ffmpeg_smoke
python manage.py test --parallel 4
cd terraform/environments/dev
terraform fmt -check -recursive ../..
terraform init -backend=false
terraform validate
```

With Docker:

```bash
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Product behavior, UI changes, new viewer or creator features, and schema changes.
- Replacing FFmpeg or moving media processing to a worker or external service.
- Dependency upgrades beyond correcting automation policy and discovery paths.
- AWS resources, paid services, or Terraform resource changes.

## Delivered

- Reconciled the README and development handoff with viewer, discovery, upload,
  notification, and collection-management work merged through PR #201.
- Updated the handoff through migration `0038_searchhistory` and the current
  focused view/service boundaries.
- Restored the Docker test command to every sprint document added after the
  Shorts controller extraction that was missing it.
- Added capability-aware FFmpeg smoke-test gating for `drawtext`, `libx264`, and
  `aac`, with four focused detection regressions.
- Pointed Terraform Dependabot discovery at `/terraform`.
- Aligned Renovate's Django policy with the supported 6.1 release line.
- Updated the documented CI Terraform version to 1.16.3.

## Verification results

- `python manage.py check` passed with no issues.
- `python manage.py makemigrations --check --dry-run` reported no changes.
- All five focused FFmpeg tests passed or skipped as designed: four capability
  tests passed and the real-binary smoke test skipped because the host FFmpeg
  lacks `drawtext`.
- All 692 tests passed with four parallel workers; the same real-binary test was
  the sole intentional skip.
- Renovate JSON parsing passed.
- Terraform formatting, initialization, and validation passed.
- `docker compose config --quiet` passed. The full container suite could not
  start because the Docker daemon socket was not present in the delivery
  environment; `docker compose run --build --rm test` remains the required local
  verification command and Docker remains the guaranteed FFmpeg environment.
