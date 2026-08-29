# Shorts Overlay Font Portability Sprint

## Sprint goal

Make generated Shorts text overlays portable across the supported Docker workflow and direct local development environments instead of depending on a Linux-only absolute font path.

## Scope

- Remove the hard-coded `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf` drawtext path.
- Let FFmpeg/fontconfig resolve the existing DejaVu Sans bold face by family/style.
- Preserve overlay text, placement, size, box, and encoding behavior.
- Add focused command-construction regression coverage.

## Acceptance criteria

- Overlay rendering no longer embeds a Linux filesystem path in the FFmpeg filter.
- Docker remains compatible with the existing `fonts-dejavu-core` package.
- Direct FFmpeg installations with fontconfig can resolve the font without the Linux path layout.
- Shorts without overlays do not receive a drawtext filter.
- No schema, migration, UI, cloud, paid-service, or dependency changes.

## Test plan

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_overlay_font
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope

- User-selectable fonts.
- Font uploads.
- New font packages.
- Changes to overlay styling or positioning.
- AWS or paid rendering services.
