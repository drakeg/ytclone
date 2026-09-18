# Playlist Library Pagination Sprint

## Goal

Keep the signed-in viewer's playlist library usable as the number of owned playlists grows, without changing playlist visibility or item behavior.

## Scope

- Move the playlist-list request path into the focused playlist view module.
- Paginate owned playlists at 24 per page.
- Keep playlist ownership private and preserve existing playlist cards/counts.
- Add safe invalid/out-of-range page handling through Django's Paginator.
- Add focused regression coverage and update routing/documentation with the implementation.

## Acceptance criteria

1. Playlist library remains login-required and contains only playlists owned by the current user.
2. Results paginate at 24 playlists per page.
3. Existing playlist presentation and video counts remain available.
4. Invalid page values fall back safely; out-of-range pages resolve to the last page.
5. Previous/Next links navigate pages without changing playlist behavior.
6. Configuration, migration-drift, focused tests, and the complete suite pass before readiness.

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

- Playlist search/filtering.
- Playlist item pagination/reordering changes.
- Watch Later changes.
- Schema, migration, or dependency changes.
- External services, workers, AWS, paid services, or Terraform changes.
