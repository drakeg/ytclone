# Search and Discovery

## Delivered behavior

Search returns grouped results for videos, channels, and playlists.

### Video matching

Videos match against:

- Title
- Description
- Creator username
- Category name

Video results can be sorted by:

- Relevance
- Newest
- Oldest
- Most viewed
- Most liked

Relevance uses lightweight Django ORM annotations. Exact title matches rank highest, followed by title, creator, category, and description matches. View and publication data provide deterministic tie-breaking.

### Channel matching

Channels match against name and description. Results are ordered by subscriber count and name.

### Playlist matching and privacy

Playlists match against name and description. Visibility rules are enforced during the query:

- Public playlists may appear for anyone.
- Private playlists never appear in search.
- Unlisted playlists are hidden from general search.
- An authenticated owner may find their own unlisted playlists.

### Empty and invalid input

Blank queries return empty grouped results rather than all content. Unsupported sort values safely fall back to relevance.

## Architecture

Search logic lives in `video/services/search.py`. The Django view is responsible only for reading request parameters and rendering the grouped result page. This creates a reusable boundary for a future API or a more advanced search backend.

The current implementation intentionally uses the existing relational database and avoids Elasticsearch, OpenSearch, Redis, or embedding services. This keeps operating cost and deployment complexity low during the bootstrap stage.

## Deferred work

- Search suggestions and autocomplete
- Private search history
- PostgreSQL full-text search
- Duration, resolution, creator, and upload-date filters
- Semantic and embedding-based search
