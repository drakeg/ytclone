# Playlist Library Search Sprint

## Goal

Help signed-in viewers quickly find an owned playlist as their private playlist library grows.

## Scope

- Add optional text search to the paginated My playlists page.
- Match owned playlists by name or description, case-insensitively.
- Apply ownership and search filtering before pagination.
- Preserve the active query through Previous/Next navigation.
- Keep existing playlist cards, counts, ordering, visibility labels, and creation flow.
- Add focused regression coverage and keep verification documentation current.

## Acceptance criteria

1. Playlist library remains login-required and current-user-only.
2. Search matches playlist name or description case-insensitively.
3. Other users' playlists never appear in results.
4. Search applies before the existing 24-item pagination.
5. Pagination links preserve the active query.
6. Blank/whitespace search behaves as the unfiltered library.
7. A query-specific empty state is shown when there are no matches.
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

- Playlist-item search or reordering changes.
- Watch Later search/reordering changes.
- Public playlist discovery changes.
- Schema/migration/dependency changes.
- External services, workers, AWS, paid services, or Terraform changes.
