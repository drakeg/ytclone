# Search Metadata Suggestions Sprint

## Goal
Improve search discovery by surfacing structured video tags and hashtags in the existing bounded autocomplete suggestions.

## Scope
- Suggest structured tags when the query matches tag names.
- Suggest hashtags with a leading `#` when the query targets hashtag names.
- Only suggest metadata attached to videos visible to the current viewer.
- Preserve existing video-title, channel, and playlist suggestions.
- Preserve the existing eight-result default limit and case-insensitive deduplication.
- Keep the current progressive-enhancement search UI and JSON endpoint unchanged.

## Acceptance criteria
- A tag attached to at least one visible video can appear as a suggestion.
- A hashtag attached to at least one visible video can appear as `#name`.
- Metadata attached only to inaccessible videos is never suggested.
- Queries beginning with `#` prioritize hashtag suggestions and do not emit a doubled prefix.
- Plain queries can surface matching tags and hashtags without changing full-search semantics.
- Duplicate values remain collapsed case-insensitively and the configured result limit is respected.
- Existing title/channel/playlist visibility behavior remains intact.

## Architecture
- Extend `video/services/search.py::search_suggestions` only; keep the existing endpoint contract returning a string list.
- Reuse `Video.objects.visible_to(user)` as the visibility source of truth.
- Filter `Tag` and `Hashtag` through their `videos` many-to-many relationship against the visible-video queryset.
- Keep all work database-local with no schema or dependency changes.

## Out of scope
- Search history.
- Fuzzy matching or typo correction.
- Ranking redesign for full search results.
- New suggestion UI components.
- External search services, workers, AWS resources, or paid infrastructure.

## Validation
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- focused search suggestion tests
- full test suite
