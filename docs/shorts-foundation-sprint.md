# Shorts Foundation Sprint

## Goal

Make Shorts a first-class content format with a dedicated creator/upload path and viewer discovery/watch experience, while reusing the existing visibility, moderation, monetization, comments, reporting, analytics, tags, hashtags, and notification foundations.

## Design

A `Video.content_type` field distinguishes standard videos from Shorts. Shorts remain ordinary `Video` rows so existing publication, audience, paid-member, moderation, reporting, reactions, comments, watch telemetry, and channel ownership rules continue to apply without parallel authorization logic.

The first Shorts experience is a dedicated vertical feed at `/videos/shorts/`. It shows one visible Short at a time in a tall player card with familiar creator, reaction, comment, and report actions. The feed is server-rendered and paginated/scrollable without requiring a new client framework or recommendation service.

Creators can explicitly choose **Video** or **Short** during upload/edit. This sprint does not attempt to inspect/crop/transcode video dimensions in-process. A later "Create Short from video" sprint can create derived Short rows that reference a source video and clip timestamps without redesigning the content-type model.

## Acceptance criteria

- `Video` supports `video` and `short` content types, defaulting existing/new legacy behavior to `video`.
- Upload/edit forms let creators choose the content type without making Shorts mandatory.
- A dedicated Shorts route/feed contains only Shorts that pass `Video.objects.visible_to(user)`.
- Standard discovery/video lists do not lose existing videos; Shorts may be surfaced separately rather than replacing long-form sections.
- Shorts use the existing video detail/comments/reactions/reporting/member-only/publication/moderation behavior.
- Channel pages distinguish Shorts from standard uploads.
- Creator library clearly identifies Shorts.
- Navigation includes a Shorts destination for viewers and creators.
- Existing videos migrate safely to standard `video` content type.
- No media transcoding, FFmpeg dependency, background worker, ML service, AWS resource, or paid service is introduced.

## Future implementation: Create Shorts from long-form videos

The next-generation clip workflow should build on this foundation rather than modify the original upload. Proposed direction:

- Creator selects one of their source videos.
- Creator chooses start/end timestamps (initially manual).
- A derived Short records source video + clip timestamps.
- A processing service creates the vertical clip/transcode asynchronously once a worker/media-processing architecture is approved.
- Later enhancements can suggest clips using chapters, retention peaks, transcript moments, or AI assistance.
- Source ownership, visibility, moderation, and deletion relationships must be explicit and auditable.

## Out of scope

- Automatic aspect-ratio/duration detection
- Forced 9:16 cropping
- FFmpeg/transcoding
- Automatic clip generation
- AI highlight detection
- Music library/licensing
- Remix/duet features
- Infinite client-side swipe application
- New AWS/Terraform infrastructure

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts
python manage.py test --parallel 4
docker compose run --build --rm test
```
