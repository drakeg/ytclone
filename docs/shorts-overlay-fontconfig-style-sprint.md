# Shorts Overlay Fontconfig Style Fix Sprint

## Goal

Correct the FFmpeg `drawtext` font selection introduced by the portability sprint so real FFmpeg accepts the filter while still avoiding Linux-only absolute font paths.

## Problem

The portable overlay implementation emitted `fontstyle=Bold` as a `drawtext` option. FFmpeg exposes `font` and `fontfile` for font selection, but not a standalone `fontstyle` option. Unit tests mocked `subprocess.run`, so they validated command construction without exercising FFmpeg's filter parser.

## Scope

- Replace the invalid `fontstyle=Bold` option with an escaped fontconfig style pattern in the `font` option.
- Keep DejaVu Sans Bold as the requested face.
- Keep the renderer independent of Linux-specific font file paths.
- Strengthen command-construction regression coverage so `fontstyle=` cannot return unnoticed.

## Acceptance criteria

- The generated filter contains `font='DejaVu Sans\\:style=Bold'`.
- The generated filter contains no `fontstyle=` drawtext option.
- No `/usr/share/fonts/...` absolute path is reintroduced.
- Overlay text, position, sizing, background box, encoding, reframing, and thumbnail behavior remain unchanged.
- No schema, migration, UI, dependency, cloud, paid-service, worker, queue, AWS, or Terraform changes.

## Verification

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_overlay_font
python manage.py test --parallel 4
docker compose run --build --rm test
```

## Out of scope

- User-selectable fonts.
- Bundling additional font files.
- Changing overlay visual styling.
- Moving FFmpeg processing to an external service.
