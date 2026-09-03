# CI / Docker Pip Install Optimization Sprint

## Goal

Reduce avoidable network work in CI and Docker builds without changing application dependencies or runtime behavior.

## Change

- Stop upgrading pip on every GitHub Actions run before installing `requirements.txt`.
- Stop upgrading pip in the Docker image before installing `requirements.txt`.
- Keep the existing `actions/setup-python` pip cache enabled.
- Keep `PIP_DISABLE_PIP_VERSION_CHECK=1` explicit in CI and Docker so dependency installation does not spend time checking for a newer pip release.

## Why

The project does not require a specific newer pip feature. Reaching the package index to self-upgrade pip adds an unnecessary network-dependent step to every cold CI run and every invalidated Docker dependency layer. The Python base image already ships with a working pip suitable for installing this repository's requirements.

## Boundaries

- No application code change.
- No dependency version change.
- No database/schema/migration change.
- No Docker runtime behavior change.
- No cloud, AWS, paid service, worker, or queue change.

## Acceptance criteria

- CI installs only the project requirements.
- Docker installs only the project requirements.
- Existing pip caching remains enabled in GitHub Actions.
- The normal Django checks and full test suite continue to pass.
- The Docker test service continues to build and run successfully.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --parallel 4
docker compose run --build --rm test
```
