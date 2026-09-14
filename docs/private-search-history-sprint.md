# Private Search History Sprint

## Goal
Make repeated discovery faster for signed-in viewers by keeping a small private list of their recent searches without exposing search activity to creators or other users.

## Scope
- Record non-blank searches for authenticated viewers only.
- Keep one row per viewer/query and refresh its recency when the query is searched again.
- Show up to 10 recent searches on the blank Search page, newest first.
- Let viewers rerun a recent search with one click.
- Let viewers clear their own search history with a POST-only action.
- Keep anonymous search behavior unchanged and untracked.

## Acceptance criteria
- Search history is private to the authenticated viewer.
- Blank searches are never recorded.
- Repeating the same normalized query does not create a duplicate row.
- The blank Search page shows at most 10 recent queries in newest-first order.
- Clearing history affects only the current viewer and requires POST.
- Search filters, pagination, suggestions, and result visibility continue to work unchanged.
- Creator analytics and channel administration never receive viewer search history.

## Architecture
- Persist viewer/query recency in a dedicated Django model with a unique `(user, query)` constraint.
- Keep recording, retrieval, and clearing logic in a focused search-history service.
- Record history from the existing search view after query normalization.
- Add a focused POST endpoint for clearing the current viewer's history.
- No external service, worker, cache, AWS resource, or paid infrastructure.

## Out of scope
- Search-history synchronization across anonymous sessions.
- Search-history suggestions inside the autocomplete dropdown.
- Per-entry deletion.
- Search analytics for creators or administrators.
- Typo correction, semantic search, PostgreSQL full-text search, Elasticsearch, or OpenSearch.

## Validation
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- focused private search-history tests
- full test suite
