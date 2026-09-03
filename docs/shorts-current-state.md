# Shorts Current State

This document is the current architecture handoff for the Shorts feature after the immersive-feed and progressive-enhancement sprints. It complements the individual sprint records without requiring contributors to reconstruct the feature from a long sequence of pull requests.

## Viewer experience

- `/videos/shorts/` is the dedicated immersive Shorts feed.
- The feed uses vertical scroll snapping and keeps one Short focused at a time.
- The active Short auto-plays; off-screen Shorts pause.
- Arrow Up/Down and Page Up/Page Down move between Shorts.
- Space toggles playback when focus is not inside an interactive control.
- Sound preference follows the viewer across Shorts in the current page session.
- Native touch scrolling remains available on mobile.
- Reduced-motion preferences disable smooth feed movement.
- Sharing uses Web Share when available and clipboard fallbacks otherwise.

## Inline social interactions

The immersive feed supports progressive enhancement. JavaScript-capable browsers keep playback and feed position while server-rendered form fallbacks remain functional.

- Like and dislike update through AJAX and use the server response as authoritative state.
- Subscribe and unsubscribe update through AJAX and retain the safe `next` fallback.
- Top-level comments post through AJAX, appear immediately, and update the visible comment count.
- Replies post through AJAX, appear immediately, and update the parent reply count.
- Dynamically inserted comments receive functional reply forms.
- Failed comment/reply submissions retain typed text and expose an inline error.
- Structured stale-CSRF responses surface the server retry guidance while unrelated failures retain generic controller errors.
- CSRF protection remains enabled for every POST path.

## Server and browser boundaries

- `video/shorts_views.py` owns Shorts feed, reaction, comment, reply, create-from-source, and re-render endpoints.
- `video/subscription_views.py` owns subscription mutation and its AJAX response contract.
- `video/services/short_clips.py` owns local FFmpeg clip generation, reframing, overlays, and source-frame thumbnail generation.
- `video/static/video/shorts.css` owns the immersive feed layout, responsive rules, and reduced-motion presentation and loads only on the Shorts feed route.
- `video/static/video/shorts_feed.js` owns feed initialization, navigation, autoplay, sound, visibility lifecycle, and visible Play/Pause text/styling.
- `video/static/video/shorts_reply_ajax.js` owns progressive enhancement for both top-level comments and replies, including dynamically inserted reply forms.
- `video/static/video/shorts_reaction_ajax.js` is the sole JavaScript owner of Shorts Like/Dislike AJAX behavior and serializes reaction changes per Short.
- `video/static/video/shorts_playback_accessibility.js` is the sole owner of dynamic playback ARIA state and keeps command-button labels synchronized.
- `video/static/video/shorts_share.js` is the sole JavaScript owner of native sharing and clipboard fallbacks.
- `video/static/video/shorts_subscription_ajax.js` is the sole JavaScript owner of subscribe/unsubscribe progressive enhancement.
- `video/templates/videos/shorts_feed.html` owns server-rendered feed markup but contains neither executable JavaScript nor inline Shorts CSS.
- Standard HTML POST redirects resolve the named `shorts_feed` route and preserve the current Short anchor.

## Query behavior

The feed intentionally preloads the data required by its template:

- video author
- channel and channel owner
- category
- likes and dislikes
- tags and hashtags
- visible top-level comments and visible replies

`channel__owner` is explicitly selected because the template checks whether the current viewer owns the channel before rendering Subscribe. A query-scaling regression test protects against restoring the previous per-Short owner lookup.

## Creator workflow

- Shorts are first-class `Video` rows with `VideoShort` metadata.
- Upload can identify qualifying portrait/square videos as Shorts.
- Creators can derive a Short from a standard source video with local FFmpeg.
- Derived Shorts retain source linkage and clip timestamps.
- Creators can select left, center, or right vertical reframing.
- Creators can add text overlays and choose overlay placement.
- Creators can select a source frame for the thumbnail.
- Derived Shorts can be re-rendered from the source while retaining their identity.
- Docker-backed tests exercise real FFmpeg clip, overlay/fontconfig, and thumbnail generation with a tiny synthetic local source.

## Security and fallback behavior

- Visibility rules are applied before Shorts reactions, comments, and replies are accepted.
- Standard videos cannot use Shorts-only mutation endpoints.
- Replies are limited to visible top-level comments; nested replies are rejected.
- Subscription redirects validate same-origin destinations.
- Stale AJAX CSRF failures return structured JSON and the enhanced controllers surface the server retry message; normal stale-form submissions use the application's friendly recovery path.
- No Shorts endpoint uses `csrf_exempt`.

## Known follow-up debt

These are maintenance candidates, not delivered behavior:

1. **Feed playback listener consolidation** — the feed controller still attaches playback/click listeners per video for visible button state while the accessibility helper already uses delegated playback events. Consider a focused delegation cleanup only if it can preserve playback behavior and controller ownership.

## Verification baseline

Shorts changes should continue to run the repository's normal checks:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --parallel 4
docker compose run --build --rm test
```

Focused tests for the affected Shorts behavior should be run before the full suite. No AWS, paid service, live payment, or recurring-spend activation is required for the current Shorts implementation.
