# Shorts Query Scaling Sprint

## Goal
Prevent the immersive Shorts feed from issuing one additional database query per channel owner rendered in the template.

## Scope
- Preload `channel__owner` with the existing Shorts feed `select_related` graph.
- Add regression coverage that compares feed query counts with one Short versus multiple Shorts on distinct channels.
- Preserve all feed behavior, visibility, comments/replies, reactions, subscriptions, and AJAX functionality.

## Acceptance criteria
1. Rendering `video.channel.owner` does not trigger a per-Short query.
2. Feed query count remains essentially constant as additional Shorts from distinct channels are added.
3. No schema or migration change is introduced.
4. No UI behavior changes.
5. No external API, cloud service, paid dependency, worker, queue, AWS resource, or Terraform change.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_query_scaling
python manage.py test --parallel 4
docker compose run --build --rm test
```
