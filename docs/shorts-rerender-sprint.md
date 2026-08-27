# Derived Short Re-render Sprint

## Goal
Allow creators to revisit a Short generated from one of their standard videos, adjust the source clip range and framing, and safely re-render the existing Short without creating a second Video row.

## Scope
- Add an **Edit source clip** action for derived Shorts that retain `VideoShort.source_video` metadata.
- Reuse the existing visual clip selector and framing controls.
- Prepopulate start/end/framing from `VideoShort` metadata.
- Render replacement media from the original source with the existing local FFmpeg pipeline.
- Preserve the Short's identity, title/description, channel, publication state, comments, analytics, reactions, and URL.
- Update source clip metadata only after a successful render.
- Delete the previous generated media only after the database update succeeds.
- On render/database failure, keep the existing Short media and metadata intact and clean up any newly generated file.
- Enforce existing creator/channel edit permissions.

## Acceptance criteria
1. Only an authorized editor can open or submit the re-render page.
2. Only Shorts with a valid source video can be re-rendered.
3. The editor starts with the stored clip range and framing selection.
4. Successful re-render replaces only the Short media and source metadata; the Video primary key and publication state are unchanged.
5. Failed FFmpeg conversion leaves the current Short untouched.
6. Invalid ranges/framing are rejected using the same rules as initial Short creation.
7. Existing Short creation behavior remains unchanged.

## Tests
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_rerender
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Architecture boundaries
- No schema or migration change.
- No cloud transcoding, queue, worker, external API, AWS resource, paid service, or Terraform change.
- Continue using storage-agnostic temporary files so local and future object storage remain supported.

## Out of scope
- Text/caption overlays.
- Automatic subject tracking or AI reframing.
- Re-rendering directly uploaded Shorts that have no source-video relationship.
- Replacing the original long-form source video.
