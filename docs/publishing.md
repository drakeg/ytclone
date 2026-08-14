# Draft and Scheduled Publishing

## Delivered behavior

Creators can save drafts, publish immediately, or schedule visibility while unpublished content remains private across public surfaces.

## Delivered safeguards

- Existing videos remain published after migration.
- Drafts and future scheduled videos are visible only to their author.
- Scheduled videos become publicly readable when their publication time arrives, without a worker.
- Public search, discovery, channel, category, profile, playlist, and history surfaces exclude unpublished videos.
- Forms require a future time for scheduled status and clear irrelevant timestamps.
- Immediate public uploads notify subscribers; scheduled-delivery notifications remain deferred.

## Architecture and testing

A `VideoQuerySet.visible_to(user)` policy centralizes visibility. `Video` has publication status and an optional publication time. Dynamic time evaluation avoids background infrastructure. Immediate uploads notify subscribers; scheduled-delivery notifications remain deferred.

The sprint-close non-Docker run passed Django checks, reported no migration drift, and completed all 105 tests. Docker is unavailable on the delivery host; run `docker compose run --rm test` on a Docker-enabled machine.

Migration `0008_video_publication` preserves every existing video as published. No dependencies, environment variables, AWS resources, workers, or external services are added.

## Out of scope

- Background publication jobs and scheduled notification delivery
- Unlisted videos and share tokens
- Time-zone selection per user
- Approval workflows and channel teams
