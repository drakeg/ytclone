# Search and Discovery

This document is created at sprint start and will be updated when the sprint closes.

## Planned behavior

Search will return grouped results for videos, channels, and playlists. Video results will support relevance, newest, oldest, most-viewed, and most-liked sorting.

Playlist visibility rules apply to discovery:

- Public playlists may appear for anyone.
- Private playlists never appear in search.
- Unlisted playlists do not appear for other users; an authenticated owner may find their own unlisted playlists.

The initial implementation uses Django ORM queries and lightweight database annotations. It intentionally avoids external search infrastructure so the feature remains inexpensive to operate during the bootstrap stage.
