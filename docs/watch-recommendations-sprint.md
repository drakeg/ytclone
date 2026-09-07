# Watch Recommendations Sprint

## Goal
Make the watch page a better continuation point by showing a small, relevant set of other long-form videos a viewer can watch next.

## Scope
- Add a bounded recommendation service for standard videos.
- Prefer videos sharing the current video's category, then channel, then broader visible catalog candidates.
- Exclude the current video and Shorts.
- Reuse `Video.objects.visible_to(user)` so private, draft, scheduled, members-only, and other restricted content cannot leak.
- Render up to 8 recommendations in a Watch next section after the watch-page content.
- Keep the existing video player, comments, Q&A, bookmarks, playlists, and watch tracking behavior unchanged.

## Acceptance criteria
- Recommendations never include the current video.
- Shorts are excluded.
- Visibility policy is respected for anonymous and authenticated viewers.
- Same-category candidates rank ahead of same-channel-only candidates, with deterministic newest-first tie breaking.
- Duplicate candidates are not rendered.
- At most 8 recommendations are returned.
- The watch page remains functional when no recommendations exist.

## Architecture
- Recommendation selection lives in `video/services/recommendations.py`.
- A focused inclusion tag renders `videos/_watch_recommendations.html` only on normal `video_detail` pages.
- The recommendation service receives the current video and request user and reuses the centralized visibility queryset.
- Existing video card/media fields are reused; no schema change.

## Validation
GitHub Actions run `34126709215` completed successfully on the implementation head. Dependency installation, Django configuration checks, migration drift checks, and the full test suite all passed.

The focused coverage verifies ranking, current-video exclusion, Shorts exclusion, hidden-content exclusion, the eight-item bound, deterministic recency ordering, and watch-page rendering.

## Out of scope
- Personalized machine-learning ranking.
- Watch-history profiling or recommendation persistence.
- Shorts recommendations.
- Autoplay-next behavior.
- Schema changes, new packages, external services, workers, AWS resources, or paid infrastructure.
