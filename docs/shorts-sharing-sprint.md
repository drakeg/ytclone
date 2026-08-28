# Shorts Sharing Sprint

## Goal
Let viewers share a Short directly from the immersive feed without leaving playback.

## Scope
- Add a Share button to each Short.
- Share the canonical video detail URL so links work independently of feed position.
- Use the Web Share API when supported by the browser.
- Fall back to the Clipboard API when native sharing is unavailable.
- Provide a legacy copy fallback when Clipboard API support is unavailable.
- Give brief in-button success/failure feedback without disrupting playback.
- Treat user-cancelled native share dialogs as a normal no-op.

## Acceptance criteria
1. Every visible Short has an accessible Share control.
2. The control targets the Short's canonical `video_detail` URL rather than a fragile feed anchor.
3. Browsers with `navigator.share` receive the title and absolute URL.
4. Other browsers copy the URL to the clipboard where possible.
5. Clipboard fallback failure is surfaced briefly without navigating away or throwing into the feed.
6. Existing playback, sound, navigation, reactions, subscriptions, comments, replies, reporting, and visibility behavior remains unchanged.
7. No schema, migration, external service, worker, queue, AWS resource, paid dependency, or Terraform change is introduced.

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_sharing
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope
- Server-side social network integrations.
- Share-count analytics.
- Custom short-link service.
- Open Graph metadata changes.
- QR-code generation.
