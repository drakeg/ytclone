# Unlisted Video Sharing

## Delivered behavior

Creators can share an unpublished video through a hard-to-guess, revocable link without exposing it through public discovery surfaces.

## Delivered safeguards

- Unlisted videos remain absent from search, discovery, channels, categories, profiles, public playlists, and other users' history.
- A valid share token grants direct viewing without authentication.
- Normal video URLs remain owner-only for unlisted videos.
- Only the author can view or rotate the share link.
- Rotating the token immediately invalidates the previous URL and accepts POST only.
- Draft and future scheduled videos cannot be accessed through a share token.

## Architecture and testing

`Video` has a unique UUID share token and an unlisted publication state. A dedicated share route resolves only unlisted videos by token. Token rotation uses a POST-only owner route and invalidates the previous URL immediately.

The sprint-close non-Docker run passed Django checks, reported no migration drift, and completed all 112 tests. Docker is unavailable on the delivery host; run `docker compose run --rm test` on a Docker-enabled machine.

Migration `0009_video_unlisted_share_token` gives every video a unique token and adds the unlisted status. No dependencies, environment variables, AWS resources, workers, or external services are added.

## Out of scope

- Password-protected links
- Link expiration dates and access limits
- Viewer identity or access auditing
- Share-link notifications
- Signed CDN URLs beyond existing media-storage behavior
