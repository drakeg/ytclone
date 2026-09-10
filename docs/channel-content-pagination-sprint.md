# Channel Content Pagination Sprint

## Goal
Keep channel pages usable as creators accumulate large video libraries by bounding both long-form videos and Shorts with independent pagination.

## Scope
- Paginate visible standard videos on channel pages at 12 items per page.
- Paginate visible Shorts independently at 8 items per page.
- Use separate `video_page` and `short_page` query parameters so navigating one section does not reset the other.
- Preserve centralized visibility and channel availability rules.
- Preserve existing subscription controls, upload-notification preferences, monetization controls, community links, and channel management actions.
- Keep deterministic newest-first ordering for both content types.

## Acceptance criteria
- Long-form videos and Shorts remain separated.
- Each section is independently bounded and paginated.
- Pagination links preserve the other section's current page.
- Invalid, negative, and out-of-range page values are handled safely by Django paginator behavior.
- Restricted or otherwise non-visible videos do not leak through pagination.
- Empty sections retain the current clean channel-page behavior.
- No new schema or dependency is required.

## Architecture
- Keep channel visibility selection in `channel_views.channel_detail`.
- Use Django `Paginator.get_page` for forgiving page parsing.
- Continue rendering long-form content through `_video_cards.html`.
- Keep the existing Shorts card markup while feeding it a page object.

## Validation
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test video.test_channel_content_pagination`
- `python manage.py test --parallel 4`
- `docker compose run --build --rm test`

## Out of scope
- Infinite scroll.
- Client-side filtering or sorting.
- New channel tabs/routes.
- Search within a channel.
- Schema changes, new packages, external services, AWS resources, or paid infrastructure.
