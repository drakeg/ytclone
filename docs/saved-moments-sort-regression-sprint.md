# Saved Moments Sort Regression Sprint

## Goal

Close the remaining regression gap in Saved moments sorting by explicitly verifying the Oldest saved option and UI state preservation.

## Scope

- Add focused coverage for Oldest saved ordering.
- Verify list removal controls carry the active sort state.
- Keep existing Saved moments search, sorting, visibility, pagination, and deletion behavior unchanged.
- Run the normal configuration, migration-drift, focused, and full-suite gates.

## Acceptance criteria

1. Oldest saved ordering is explicitly regression-tested.
2. The Saved moments remove form preserves the active sort value.
3. Existing newest/title/timestamp sorting remains unchanged.
4. No product behavior, schema, migration, dependency, or external-service changes are introduced.
5. Focused and full CI pass before readiness.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_bookmarks
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- New Saved moments filters or sort modes.
- Bookmark schema changes.
- External services, workers, AWS, paid services, dependencies, or Terraform changes.
