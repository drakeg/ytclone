# CI Performance Sprint

## Goal

Reduce GitHub Actions feedback time without reducing test coverage or weakening production security settings.

## Current bottleneck

The Django workflow spends almost all of its runtime in `python manage.py test`; dependency installation, system checks, and migration-drift checks are comparatively small. The suite creates many test users, so production-strength password hashing is unnecessary overhead during tests.

## Scope

- Add an explicit environment-controlled fast password hasher for CI/tests only.
- Keep the production/default password hasher unchanged when the flag is absent.
- Run the full Django test suite with Django's built-in parallel test runner in GitHub Actions.
- Keep configuration checks and migration-drift checks intact.
- Compare the PR run duration with recent baseline runs before merging.

## Acceptance criteria

- Production/default settings continue to use Django's normal password hashing configuration.
- Fast hashing activates only when `DJANGO_FAST_TEST_HASHER=true` is explicitly set.
- GitHub Actions still runs the complete test suite.
- Parallel execution does not introduce test failures or shared-state flakiness.
- Configuration and migration checks remain required.
- No application behavior, database schema, dependencies, AWS resources, or paid services change.

## Verification

```bash
DJANGO_FAST_TEST_HASHER=true python manage.py check
DJANGO_FAST_TEST_HASHER=true python manage.py makemigrations --check --dry-run
DJANGO_FAST_TEST_HASHER=true python manage.py test --parallel 4
```

If parallel execution proves unstable, retain the fast hasher and revert CI to serial full-suite execution rather than weakening or skipping tests.
