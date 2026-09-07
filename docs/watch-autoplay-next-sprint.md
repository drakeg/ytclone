# Watch Autoplay Next Sprint

## Goal
Build on the new Watch next recommendations by giving viewers an optional, persistent autoplay path to the highest-ranked next video.

## Scope
- Add an Autoplay on/off control to Watch next when recommendations exist.
- Treat the first server-ranked recommendation as the next video.
- Start a five-second announced countdown when the current long-form video ends.
- Cancel the countdown if playback resumes or the viewer turns autoplay off.
- Persist the browser preference with local storage; default to enabled when no preference exists.
- Load the controller only on normal video detail pages.

## Acceptance criteria
- Autoplay never runs when there is no visible recommendation.
- The next destination comes from the existing visibility-safe recommendation service rather than a client-generated URL.
- The viewer can disable autoplay before or during the countdown.
- The setting persists across watch pages when browser storage is available.
- Storage failures do not break normal playback or navigation.
- Countdown status is exposed through an `aria-live` region.
- Existing player controls, comments, Q&A, bookmarks, playlists, watch tracking, and ordinary recommendation links remain unchanged.

## Architecture
- `video/services/recommendations.py` remains the sole owner of recommendation ranking and visibility.
- `_watch_recommendations.html` exposes the first ranked destination and progressive-enhancement controls.
- `video/static/video/watch_autoplay_next.js` owns preference, countdown, cancellation, and navigation behavior.
- No backend mutation or persistence is required.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_watch_recommendations video.test_watch_autoplay_next
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope
- Server-side autoplay preferences.
- Personalized/ML recommendations.
- Preloading the next media file.
- Shorts autoplay changes.
- Schema changes, new dependencies, external services, workers, AWS resources, paid infrastructure, or Terraform changes.
