# Watch Later Sort Regression Sprint

## Goal

Close the remaining Watch Later sort regression gap by explicitly verifying Oldest saved ordering and the rendered removal state.

## Scope

- Add explicit Oldest saved ordering coverage.
- Verify the Watch Later removal control preserves active query, sort, and page state.
- Keep current search, visibility, pagination, and sorting behavior unchanged.

## Acceptance criteria

1. Oldest saved ordering is explicitly regression-tested.
2. Removal UI carries active query, sort, and page values.
3. Existing newest/title sorting and visibility boundaries remain unchanged.
4. No product behavior, schema, migration, dependency, or infrastructure changes.
5. Focused and full CI pass before readiness.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_watch_later
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- New Watch Later filters or sort modes.
- Manual Watch Later ordering.
- External services, workers, AWS, paid services, dependencies, or Terraform changes.
