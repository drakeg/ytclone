# Shorts Static CSS Extraction Sprint

## Goal

Move the immersive Shorts feed stylesheet out of the Django template and into the app's static namespace without changing layout, responsive behavior, reduced-motion behavior, playback, social interactions, or server-rendered fallbacks.

## Scope

- Move the existing inline Shorts CSS to `video/static/video/shorts.css` without changing selectors or declarations.
- Load the stylesheet only for the named `shorts_feed` route.
- Remove the inline `<style>` block from `video/templates/videos/shorts_feed.html`.
- Preserve all existing Shorts markup and JavaScript controller boundaries.
- Add focused regression coverage for route-scoped loading, absence of inline CSS, and preservation of responsive/reduced-motion rules.
- Refresh the Shorts architecture handoff so controller ownership matches the post-#163 implementation.

## Acceptance criteria

- The Shorts feed response references `video/shorts.css`.
- Non-Shorts pages do not load `video/shorts.css`.
- The Shorts template contains no inline `<style>` block.
- The extracted stylesheet retains the existing mobile breakpoint and `prefers-reduced-motion` rules.
- No backend, schema, migration, dependency, JavaScript behavior, AWS resource, Terraform configuration, external service, worker, queue, or paid service changes are introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_feed_controller
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Architecture decision

The stylesheet is loaded from `base.html` behind the same named-route guard used for the Shorts JavaScript controllers. This keeps the asset out of unrelated pages while allowing the child template to remain markup-only. The CSS contents are moved without intentional visual changes so this sprint remains a maintenance extraction rather than a redesign.
