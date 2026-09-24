# Watch Later Bulk Removal Sprint

## Goal

Let signed-in viewers remove multiple visible videos from their private Watch Later queue in one action without weakening privacy or visibility boundaries.

## Scope

- Add checkbox selection to the Watch Later list.
- Add a POST-only bulk removal endpoint.
- Restrict removal to selected videos in the current viewer's private Watch Later playlist that are also currently visible to that viewer.
- Ignore malformed, duplicate, forged, other-user, and inaccessible video IDs.
- Preserve active search, sort, and page state after bulk removal.
- Keep the existing single-video Watch Later action unchanged across all other video-card surfaces.
- Add focused regression coverage for ownership, visibility, malformed input, state preservation, and empty selection.

## Acceptance criteria

1. A viewer can select and remove multiple visible Watch Later videos.
2. Another user's Watch Later queue cannot be changed through forged IDs.
3. Videos no longer visible to the viewer cannot be removed through the bulk-list endpoint.
4. Empty, malformed, duplicate, and non-Watch-Later IDs are safe.
5. Search, sort, and page state are preserved after the action.
6. The bulk endpoint rejects GET.
7. Bulk checkboxes render only on Watch Later, not on shared video-card surfaces elsewhere.
8. No schema, migration, dependency, external-service, AWS, paid-service, worker, queue, or Terraform changes.
9. Focused and full CI pass before readiness.

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

- Drag-and-drop/manual Watch Later ordering.
- Completion-based automatic cleanup.
- Bulk actions on unrelated playlists or browsing surfaces.
- Background retention or expiry policies.
