# Watch Recommendations Sprint

## Goal
Make the watch page a better continuation point by showing a small, relevant set of other long-form videos a viewer can watch next.

## Scope
- Add a bounded recommendation service for standard videos.
- Prefer videos sharing the current video's category, then channel, then broader visible catalog candidates.
- Exclude the current video and Shorts.
- Reuse `Video.objects.visible_to(user)` so private, draft, scheduled, members-only, and other restricted content cannot leak.
- Render up to 8 recommendations in the existing watch sidebar below creator/save controls.
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
- Put recommendation selection in a focused `video/services/recommendations.py` service.
- Keep `_render_video_detail` responsible for passing the current video/user into the service and adding the result to template context.
- Reuse existing video card/media fields; no schema change.

## Local validation
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test video.test_watch_recommendations`
- `python manage.py test --parallel 4`
- `docker compose run --build --rm test`

## Out of scope
- Personalized machine-learning ranking.
- Watch-history profiling or recommendation persistence.
- Shorts recommendations.
- Autoplay-next behavior.
- Schema changes, new packages, external services, workers, AWS resources, or paid infrastructure.
