# Homepage Discovery

## Delivered behavior

The homepage replaces the previous chronological video list with useful, privacy-safe discovery sections powered by Django ORM queries.

## Sections

The homepage will show bounded sections for:

- Continue Watching for authenticated users with unfinished playback
- Newest videos
- Most viewed videos
- Most liked videos
- Recently watched videos for authenticated users
- Recently updated public playlists

Anonymous visitors will not receive Continue Watching or recently watched sections. Empty sections will render a clear message rather than broken or misleading content.

## Behavior and privacy

- Newest videos are ordered by publication date.
- Most viewed videos are ordered by view count.
- Most liked videos are ordered by an annotated like count.
- Recently watched videos are unique, ordered by the current user's most recent watch time, and never expose another user's history.
- Continue Watching uses the current user's private progress, is ordered by most recent activity, and excludes completed or near-complete videos.
- Only public playlists appear, regardless of authentication.
- Each section is limited to four results so the homepage remains bounded.
- Query construction lives in a discovery service rather than the view.
- The homepage handles a completely empty database.

## Architecture

Discovery query construction lives in `video/services/discovery.py`. The homepage view passes the current user to that service and renders the returned sections. This keeps the view small and provides a stable boundary for future recommendation logic.

The sprint uses the existing relational database and Django ORM. It introduces no background workers, caches, recommendation services, paid APIs, or AWS resources.

## Testing

`video/test_discovery.py` covers section ordering, result limits, playlist privacy, authenticated history isolation, anonymous behavior, repeated history, and empty states.

The sprint-close non-Docker run completed successfully with 54 tests. Django system checks passed and the migration-drift check reported no changes. Docker commands remain documented in the README, but could not be executed in the delivery environment because Docker was not installed.

Run the full local suite documented in the README:

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
