# Search History Item Removal Sprint

## Goal

Let signed-in viewers remove individual entries from their private recent-search history without clearing the entire list.

## Scope

- Add an owner-scoped service operation for deleting one SearchHistory entry.
- Extend the existing search POST workflow with an individual remove action.
- Add a Remove control beside each recent search while preserving one-click replay.
- Keep Clear history behavior unchanged.
- Add focused privacy, POST-action, and UI regression coverage.

## Acceptance criteria

1. Search history remains private to the signed-in viewer.
2. A viewer can remove one of their own recent searches.
3. A viewer cannot remove another user's search-history entry.
4. Removal is POST-only through the existing search endpoint.
5. Removing one entry leaves the viewer's other recent searches intact.
6. Clear history continues to remove all current-viewer entries only.
7. Anonymous mutations remain forbidden and unknown actions remain rejected.
8. Configuration, migration-drift, focused tests, and full suite pass before readiness.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_private_search_history
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Search-history pagination, retention schedules, or bulk selection.
- Changes to search ranking, suggestions, or result filters.
- Schema/migration/dependency changes.
- External services, workers, AWS, paid services, or Terraform changes.
