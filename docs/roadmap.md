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
- Grouped Search and Discovery across videos, channels, and visible playlists

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

## Next sprint candidate

Homepage discovery sections using the search and history foundations:

- Newest videos
- Most viewed videos
- Most liked videos
- Recently watched for authenticated users
- Public playlists

## Later candidates

- Continue Watching and playback-position tracking
- Creator analytics
- Notifications
- Low-cost AWS application hosting and deployment
