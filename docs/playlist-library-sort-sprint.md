# Playlist Library Sort Sprint

## Goal

Give signed-in viewers useful ordering controls for their private playlist library while preserving search, ownership boundaries, and pagination.

## Scope

- Add bounded sorting to My playlists.
- Support recently updated, oldest updated, and playlist name.
- Compose sorting with existing name/description search before pagination.
- Preserve query and sort through pagination.
- Keep the existing 24-item pagination and current-user ownership scope.
- Add focused regression coverage and current verification instructions.

## Acceptance criteria

1. My playlists remains login-required and current-user-only.
2. Default ordering remains recently updated first.
3. Valid sort options reorder only the current viewer's playlists.
4. Invalid sort values safely fall back to recently updated.
5. Search and sort compose before pagination.
6. Pagination preserves active query and sort.
7. Existing playlist detail/item ordering behavior is unchanged.
8. Configuration, migration-drift, focused tests, and full suite pass before readiness.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_playlists
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Playlist item ordering changes.
- Watch Later behavior.
- Playlist schema changes.
- External services, workers, AWS, paid services, dependencies, or Terraform changes.
