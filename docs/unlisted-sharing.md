# Unlisted Video Sharing

## Sprint goal

Let creators share an unpublished video through a hard-to-guess, revocable link without exposing it through public discovery surfaces.

## Acceptance criteria

- Unlisted videos remain absent from search, discovery, channels, categories, profiles, public playlists, and other users' history.
- A valid share token grants direct viewing without authentication.
- Normal video URLs remain owner-only for unlisted videos.
- Only the author can view or rotate the share link.
- Rotating the token immediately invalidates the previous URL and accepts POST only.
- Draft and future scheduled videos cannot be accessed through a share token.

## Architecture and testing

`Video` gains a unique UUID share token and an unlisted publication state. A dedicated share route resolves only unlisted videos by token. Token rotation uses a POST-only owner route. Focused tests cover surface privacy, valid and invalid links, owner controls, token rotation, and draft/scheduled isolation.

Run the full suite locally or with `docker compose run --rm test` as documented in the README.

## Out of scope

- Password-protected links
- Link expiration dates and access limits
- Viewer identity or access auditing
- Share-link notifications
- Signed CDN URLs beyond existing media-storage behavior
