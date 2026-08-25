# Personalized Discovery Sprint

## Goal

Make the authenticated homepage feel personally useful using only private first-party signals the application already stores, while keeping recommendations understandable, bounded, privacy-preserving, and free of external recommendation infrastructure.

## Scope

- Keep Continue Watching as the highest-priority authenticated section.
- Add a bounded **From channels you follow** section based on free channel subscriptions.
- Add a bounded **Because you watched** section using topic overlap from recently watched videos (category, structured tags, and hashtags).
- Add a bounded **Topics you watch** section that surfaces the viewer's strongest recent structured tags/hashtags and links them to existing search/hashtag discovery.
- Keep anonymous discovery unchanged.
- Route every recommended video through `Video.objects.visible_to(user)`.
- Keep all personalization private to the current viewer; creators receive no viewer-level recommendation/profile data.
- Put ranking/query logic in `video/services/discovery.py`.

## Acceptance criteria

- Followed-channel recommendations contain only visible videos from channels the viewer subscribes to and exclude videos already watched by that viewer.
- Topic recommendations derive only from the current viewer's watch history and exclude watched videos.
- Topic recommendations favor stronger overlap and then fall back to existing popularity/recency signals deterministically.
- Topic chips are bounded and derived from recent viewing only.
- Another user's watch history never influences the current viewer's personalized sections.
- Anonymous visitors do not receive personalized sections.
- Existing publication, member-only, deleted, and scheduled visibility rules remain centralized through `visible_to()`.
- No new database schema, external service, cache, worker, ML model, AWS resource, or paid infrastructure is required.

## Out of scope

- Collaborative filtering or cross-user similarity
- Creator access to individual viewer interests
- Embeddings, semantic recommendations, external AI/ML services
- Trending decay algorithms
- Notification changes
- Infinite scrolling
- Terraform changes

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_personalized_discovery
python manage.py test
docker compose run --build --rm test
```
