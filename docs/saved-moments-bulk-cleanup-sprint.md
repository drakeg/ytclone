# Saved Moments Bulk Cleanup Sprint

## Goal

Let signed-in viewers remove multiple private Saved moments in one action without weakening bookmark ownership or video-visibility boundaries.

## Scope

- Add checkbox selection to the private Saved moments list.
- Add a POST-only bulk remove action.
- Restrict deletion to selected bookmarks owned by the current viewer and present in the viewer's visibility-safe Saved moments queryset.
- Ignore forged, malformed, duplicate, other-user, or inaccessible bookmark IDs.
- Preserve active search, sort, and page state after bulk removal.
- Keep the existing single-item Remove action unchanged.
- Add focused regression coverage for ownership, visibility, malformed input, state preservation, and empty selection.

## Acceptance criteria

1. A signed-in viewer can select and remove multiple visible Saved moments from the list.
2. Other users' bookmarks cannot be removed through forged IDs.
3. Bookmarks attached to videos not currently visible to the viewer cannot be removed through the bulk-list endpoint.
4. Empty, malformed, and duplicate selections are safe and do not delete unrelated bookmarks.
5. Search, sort, and page state are preserved after the action.
6. The endpoint rejects GET.
7. No schema, migration, dependency, external-service, AWS, paid-service, worker, queue, or Terraform changes.
8. Focused and full CI pass before readiness.

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

- Drag-and-drop or manual Saved moments ordering.
- Editing bookmark labels from the list.
- Bulk actions on the video watch page.
- Retention policies or automatic cleanup.
