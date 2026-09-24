# Bulk List Accessibility Sprint

## Goal

Harden the new bulk-selection controls on Saved moments, Watch Later, Watch History, and Notifications so keyboard and screen-reader users get clear selection controls, selected-item feedback, and safer destructive actions.

## Scope

- Add a page-level Select all checkbox to each bulk-enabled list.
- Disable destructive bulk buttons until at least one item is selected.
- Expose the current selected-item count through an `aria-live` status region.
- Keep item checkbox labels specific to the corresponding saved moment, video, history entry, or notification.
- Use one small shared progressive-enhancement script across the four list pages.
- Preserve all existing no-JavaScript server-side safety behavior.
- Add focused template/static-asset regression tests.

## Acceptance criteria

1. Each bulk-enabled page provides Select all and a live selected-count status.
2. Bulk destructive buttons start disabled when JavaScript is available and become enabled only when an item is selected.
3. Selecting/deselecting all updates item checkboxes and selected count.
4. Item-level checkbox labels remain accessible and specific.
5. The script is loaded only on bulk-enabled routes.
6. Existing POST endpoints remain safe when JavaScript is unavailable.
7. No schema, migration, dependency, external-service, AWS, paid-service, worker, queue, or Terraform changes.
8. Focused and full CI pass before readiness.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_ui_design video.test_video_bookmarks video.test_watch_later video.test_watch_history video.test_notification_pagination
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```
