# Video Tags and Hashtag Discovery

## Sprint goal

Improve creator metadata and viewer discovery without adding friction to upload. Creators may add optional structured tags, while hashtags written naturally in video titles/descriptions become indexed, clickable discovery links.

## Acceptance criteria

- Structured tags are optional on upload and edit and never block publishing when omitted.
- Creators enter tags as a simple comma-separated list; duplicates and case variants normalize to one canonical tag.
- Tag names are trimmed, length-limited, and empty values are ignored.
- Existing videos remain valid with no tags.
- Video search matches structured tags in addition to existing title, description, creator, and category fields.
- Hashtags are derived automatically from title and description rather than requiring a second creator form.
- Hashtags normalize case while preserving a readable display value.
- Video detail pages show clickable structured tags and indexed hashtags.
- Hashtag pages list only videos visible to the current viewer using the existing centralized visibility rules.
- Editing title/description updates the video's indexed hashtags atomically so removed hashtags stop discovering the video.
- Core normalization/indexing logic lives in a service module.

## Architecture decisions

- Add reusable `Tag` and `Hashtag` models and many-to-many relationships from `Video`.
- Structured tags are explicit creator metadata; hashtags are derived metadata. They remain separate concepts.
- Hashtag extraction supports letters, numbers, and underscores after `#`, normalizes with Unicode-safe case folding/lowercasing, and ignores duplicate occurrences.
- Hashtag discovery queries start from `Video.objects.visible_to(user)` so private/draft/unlisted/member-only behavior is not reimplemented.
- Tag/hashtag persistence runs after a valid video save, alongside existing chapter replacement.

## Out of scope

- Autocomplete/tag suggestions
- Trending hashtag ranking or time decay
- Following tags/hashtags
- Search history or semantic search
- ML recommendations
- External search services
- AWS/Terraform changes

## Verification

```bash
python manage.py test video.test_video_metadata_discovery
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
docker compose run --build --rm test
```

No paid service or infrastructure change is required.