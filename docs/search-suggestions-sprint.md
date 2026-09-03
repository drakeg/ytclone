# Search Suggestions Sprint

## Goal

Add fast, bounded search suggestions to the existing site search without introducing a new search service, schema change, or external dependency.

## Scope

- Add a small JSON endpoint that returns suggestions derived from content the current viewer is allowed to discover.
- Reuse existing visibility rules for videos, channels, and playlists.
- Return a bounded set of concise labels suitable for autocomplete.
- Enhance both desktop and mobile search inputs with the same progressive-enhancement controller.
- Preserve ordinary GET search submission when JavaScript is unavailable or suggestions fail.
- Add focused privacy, bounding, endpoint, and browser-controller regression coverage.

## Acceptance criteria

- Suggestions are not returned for blank or one-character queries.
- Results are capped and deduplicated.
- Private videos/playlists and otherwise unavailable channels are never exposed through suggestions.
- Authenticated owners may still receive suggestions for their own discoverable unlisted playlists according to the existing search visibility policy.
- Selecting a suggestion populates the search field and submits the existing search form.
- Keyboard and pointer use remain supported through the browser-native suggestion control.
- Existing search result behavior and sorting are unchanged.

## Architecture

Suggestion query composition belongs in `video/services/search.py` beside the existing search service. The view only normalizes the request and returns JSON. The browser enhancement remains a small static controller loaded from the shared base template.

To keep the implementation simple and accessible, the controller uses a shared `datalist` per search input rather than a custom ARIA combobox. Requests are debounced and stale responses are ignored.

## Out of scope

- Search history
- Personalized or ML suggestions
- Typo correction
- Trending suggestions
- PostgreSQL full-text search, Elasticsearch, OpenSearch, or embeddings
- Database/schema/migration changes
- New packages or external services
- AWS, paid services, workers, or queues

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_search_suggestions
python manage.py test --parallel 4
docker compose run --build --rm test
```
