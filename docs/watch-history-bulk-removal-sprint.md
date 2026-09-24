# Watch History Bulk Removal Sprint

## Goal

Let signed-in viewers remove selected entries from their private Watch History without forcing an all-or-nothing Clear history action.

## Scope

- Add checkbox selection to the private Watch History page.
- Add a POST-only bulk removal endpoint.
- Restrict deletion to selected history rows owned by the current viewer and currently visible in the viewer's visibility-safe history queryset.
- Ignore malformed, duplicate, forged, other-user, and inaccessible history-entry IDs.
- Preserve active search, sort, and page state after bulk removal.
- Keep existing single-entry Remove and full Clear history behavior unchanged.
- Add focused regression coverage for ownership, visibility, malformed input, state preservation, and empty selection.

## Acceptance criteria

1. A viewer can remove multiple selected visible history entries.
2. Another user's history cannot be changed through forged IDs.
3. Entries for videos no longer visible to the viewer cannot be removed through the bulk-list endpoint.
4. Empty, malformed, duplicate, and unrelated IDs are safe.
5. Search, sort, and page state are preserved.
6. The endpoint rejects GET.
7. Existing Clear history remains full-current-viewer cleanup.
8. No schema, migration, dependency, retention-policy, external-service, AWS, paid-service, worker, queue, or Terraform changes.
9. Focused and full CI pass before readiness.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_watch_history
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Watch-history retention/expiry policy.
- Playback tracking or Continue Watching behavior.
- Reordering history.
- Bulk actions on Watch Later, Saved moments, or playlists.
