# Product Roadmap

## Delivery process

Every sprint follows this checklist:

### Before implementation

- Review the README, architecture, roadmap, AWS, Terraform, and affected feature documentation.
- Update the roadmap with the sprint goal, scope, acceptance criteria, test plan, and out-of-scope work.
- Document the local commands contributors will use to verify the sprint, including both Docker and non-Docker paths.
- Record architecture decisions before code is written.

### During implementation

- Keep the sprint and pull request focused on one concern.
- Add or update tests alongside the implementation.
- Prefer business logic in service modules rather than views.
- Update local test instructions whenever dependencies, configuration, migrations, or validation commands change.

### Before sprint closure

- Update all affected documentation to match delivered behavior and configuration.
- Record new environment variables, migrations, infrastructure, and operational notes.
- Confirm the README contains current Docker and non-Docker instructions for Django system checks, migration-drift checks, and the full unit test suite.
- When Terraform or its workflow is affected, document and run formatting and validation commands.
- Run the documented local checks, record the results in the pull request, and resolve any mismatch between the documentation and the actual commands.
- Update the roadmap with delivered work, deferred work, and next sprint candidates.

A sprint is not closed until its local test instructions are complete and reproducible.

## Completed foundation

- Environment-based secrets and production security settings
- Django 5.2 LTS dependency baseline
- Docker development and Gunicorn production runtime
- CI for Django and Terraform validation
- Authentication and authorization hardening
- Mutually exclusive reactions
- Session-based view counting
- Upload validation and configurable limits
- Optional private S3 media storage
- Terraform modules for private media storage and AWS budget alerts
- Playlists with public, unlisted, and private visibility
- Private watch history with removal and clear-all controls
- Grouped Search and Discovery across videos, channels, and visible playlists
- Homepage Discovery with newest, most viewed, most liked, recently watched, and public playlist sections
- Continue Watching with private playback progress, automatic resume, and containerized test execution

## Completed sprint: Search and Discovery

Delivered:

- Video matching by title, description, category, and creator username
- Channel matching by name and description
- Playlist matching by name and description
- Grouped result sections for videos, channels, and playlists
- Video sorting by relevance, newest, oldest, most viewed, and most liked
- Private playlists excluded from search
- Public playlists searchable by anyone
- Owners able to find their own unlisted playlists without exposing them to other users
- Search business logic isolated in `video/services/search.py`
- Regression tests for matching, visibility, sorting, invalid sort values, and blank queries

Deferred:

- Search suggestions and autocomplete
- Search history
- PostgreSQL full-text search
- Elasticsearch or OpenSearch
- Semantic or embedding search
- Duration, resolution, and upload-date filters

## Completed sprint: Homepage Discovery

Goal: replace the homepage's chronological list with bounded discovery sections built from the search, reaction, playlist, and history foundations.

- Newest videos
- Most viewed videos
- Most liked videos
- Recently watched videos for authenticated users
- Recently updated public playlists

Delivered:

- Bounded sections for newest, most viewed, and most liked videos
- Private, per-user recently watched videos for authenticated users
- Recently updated public playlists with video counts
- Privacy enforcement that excludes private and unlisted playlists
- Clear empty states and an anonymous homepage without history content
- Discovery query logic isolated in `video/services/discovery.py`
- Regression tests for ordering, limits, privacy, history isolation, anonymous behavior, and empty data

Deferred:

- Personalized recommendations beyond watch history
- Playback-position tracking and Continue Watching
- Trending time windows and ranking decay
- Featured-channel curation
- Infinite scrolling and homepage pagination
- Background workers, caches, or machine-learning recommendations

## Completed sprint: Continue Watching

Add private playback-position tracking, resumable video playback, and an unfinished-video homepage section. Also add a one-command Docker Compose test runner for the complete Django verification suite.

Delivered:

- Authenticated playback progress saved to the existing private watch-history record
- Automatic resume on the video detail page
- Continue Watching homepage section ordered by recent activity
- Completed and near-complete videos excluded from Continue Watching
- Safe endpoint validation, clamping, CSRF protection, and per-user isolation
- Migration `0005_watchhistory_playback_progress` with backward-compatible defaults
- One-command containerized verification through `docker compose run --rm test`
- Regression tests for authorization, validation, isolation, resume behavior, filtering, ordering, and homepage visibility

Deferred:

- Real-time synchronization between simultaneous players
- Chapters and bookmarks
- Playback analytics and creator reporting
- Recommendation ranking based on completion
- Background workers, caches, and external event pipelines

## Current sprint: Creator Analytics

Add a private creator dashboard for lifetime upload, view, reaction, and unique subscriber metrics using existing application data.

Acceptance criteria, architecture, privacy boundaries, local Docker and non-Docker commands, test coverage, and exclusions are documented in `docs/creator-analytics.md` before implementation begins.

## Later candidates

- Notifications
- Low-cost AWS application hosting and deployment
