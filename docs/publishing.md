# Draft and Scheduled Publishing

## Sprint goal

Let creators save drafts, publish immediately, or schedule visibility while preventing unpublished content from leaking through public pages.

## Acceptance criteria

- Existing videos remain published after migration.
- Drafts and future scheduled videos are visible only to their author.
- Scheduled videos become publicly readable when their publication time arrives, without a worker.
- Public search, discovery, channel, category, profile, playlist, and history surfaces exclude unpublished videos.
- Forms require a future time for scheduled status and clear irrelevant timestamps.
- Immediate public uploads notify subscribers; scheduled-delivery notifications remain deferred.

## Architecture and testing

A `VideoQuerySet.visible_to(user)` policy will centralize visibility. `Video` gains publication status and an optional publication time. Dynamic time evaluation avoids background infrastructure. Tests cover migration defaults, form validation, owner access, anonymous privacy, due scheduling, and public surface filtering.

Run the full suite locally or with `docker compose run --rm test` as documented in the README.

## Out of scope

- Background publication jobs and scheduled notification delivery
- Unlisted videos and share tokens
- Time-zone selection per user
- Approval workflows and channel teams
