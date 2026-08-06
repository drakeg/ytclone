# Homepage Discovery

## Sprint goal

Replace the homepage's single chronological video list with useful, privacy-safe discovery sections powered by Django ORM queries.

## Planned behavior

The homepage will show bounded sections for:

- Newest videos
- Most viewed videos
- Most liked videos
- Recently watched videos for authenticated users
- Recently updated public playlists

Anonymous visitors will not receive a recently watched section. Empty sections will render a clear message rather than broken or misleading content.

## Acceptance criteria

- Newest videos are ordered by publication date.
- Most viewed videos are ordered by view count.
- Most liked videos are ordered by an annotated like count.
- Recently watched videos are unique, ordered by the current user's most recent watch time, and never expose another user's history.
- Only public playlists appear, regardless of authentication.
- Each section has a fixed result limit so the homepage remains bounded.
- Query construction lives in a discovery service rather than the view.
- The homepage handles a completely empty database.

## Architecture

Discovery query construction will live in `video/services/discovery.py`. The homepage view will pass the current user to that service and render the returned sections. This keeps the view small and provides a stable boundary for future recommendation logic.

The sprint uses the existing relational database and Django ORM. It introduces no background workers, caches, recommendation services, paid APIs, or AWS resources.

## Test plan

Focused tests will cover section ordering, result limits, playlist privacy, authenticated history isolation, anonymous behavior, and empty states. Before closure, run the full local suite documented in the README:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

The README also documents the equivalent Docker commands. Terraform checks are not applicable unless the sprint changes files under `terraform/` or its workflow.

## Out of scope

- Personalized recommendations beyond the user's watch history
- Playback-position tracking or Continue Watching
- Trending time windows or ranking decay
- Featured-channel curation
- Infinite scrolling or homepage pagination
- Redis, Celery, search services, or machine-learning recommendations
