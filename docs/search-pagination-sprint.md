# Search Result Pagination Sprint

## Goal

Keep search responsive and usable as the video, channel, and playlist catalogs grow by bounding each result group and providing conventional pagination without changing search ranking or visibility rules.

## Scope

- Paginate video search results at 12 results per page.
- Paginate channel and playlist results at 6 results per page.
- Keep each result group independently pageable so a creator can browse more videos without losing the current channel or playlist page.
- Preserve the active search query and video sort option in every pagination link.
- Preserve the other result groups' current page parameters when one group is paged.
- Reuse the existing `search_content()` visibility and ranking querysets; pagination must not duplicate or weaken access rules.
- Keep the implementation server-rendered and dependency-free.
- Add focused view/template tests for page sizing, query preservation, invalid page values, and visibility behavior.

## Acceptance criteria

- Search never renders an unbounded matching queryset for videos, channels, or playlists.
- The first page contains at most 12 videos, 6 channels, and 6 playlists.
- Previous/next links appear only when applicable.
- Page links preserve `query`, `sort`, and the independent page values for the other result groups.
- Invalid, non-numeric, zero, negative, or out-of-range page values resolve safely rather than returning a server error.
- Existing relevance and alternate video sort orders are unchanged.
- Existing private/unlisted visibility rules remain unchanged.
- Blank search behavior remains unchanged.
- No schema migration, external search service, JavaScript framework, or new dependency is added.

## Architecture

- `video/search_views.py` becomes the focused HTTP owner for the search results page as well as suggestions.
- `django.core.paginator.Paginator` wraps the three querysets returned by `search_content()`.
- A small helper normalizes each requested page and returns the first/last valid page when the request is malformed or out of range.
- `video/templates/videos/search_results.html` renders compact independent pagination controls beneath each result group.
- `video/urls.py` routes the existing `search` URL name to `search_views.search`, so callers and bookmarks keep the same URL contract.

## Out of scope

- Infinite scroll.
- Client-side result fetching.
- Search-history persistence.
- Typo correction or fuzzy matching.
- Changes to ranking weights.
- External search/index services.
