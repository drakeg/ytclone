# Product Roadmap

## Delivery process

Every sprint begins with a documentation review and roadmap update before implementation starts. The sprint closes with documentation updated to match the delivered behavior, configuration, tests, and remaining follow-up work.

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

## Current sprint: Search and Discovery

### Goals

- Search videos by title, description, category, and creator username
- Search channels by name and description
- Search visible playlists by name and description
- Group results by videos, channels, and playlists
- Support video sorting by relevance, newest, oldest, most viewed, and most liked
- Keep private playlists out of all search results
- Allow owners to find their own unlisted playlists while keeping other users' unlisted playlists out of general search
- Introduce a small search service layer so query and ranking logic does not accumulate in views
- Add regression tests for matching, visibility, sorting, and empty queries

### Out of scope

- Search suggestions and autocomplete
- Search history
- PostgreSQL full-text search
- Elasticsearch or OpenSearch
- Semantic or embedding search
- Duration, resolution, and upload-date filters

## Next candidates

- Homepage discovery sections
- Continue Watching and playback-position tracking
- Creator analytics
- Notifications
- Low-cost AWS application hosting and deployment
