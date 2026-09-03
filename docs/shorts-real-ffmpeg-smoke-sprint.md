# Shorts Real FFmpeg Smoke Sprint

## Goal

Exercise the production Shorts media command against a real FFmpeg binary so command/filter regressions are caught before deployment.

## Scope

- Generate a tiny synthetic local source video with FFmpeg; no fixture download or network access.
- Run the existing `_run_ffmpeg` path with a text overlay so the real `drawtext`/fontconfig contract is exercised.
- Run the existing thumbnail extraction path against the same source.
- Assert both generated artifacts are non-empty.
- Skip the focused test on host environments where FFmpeg is not installed; the repository Docker image installs FFmpeg and DejaVu fonts, so Docker/CI provides the guaranteed execution environment.

## Boundaries

- No production media behavior change.
- No database/schema/migration change.
- No new Python or system dependency.
- No binary fixture committed to the repository.
- No network, cloud, AWS, paid service, worker, or queue requirement.
- Keep the generated media to roughly one second so the smoke test remains inexpensive.

## Acceptance criteria

- The real FFmpeg binary successfully creates a Short using the same helper production uses.
- The overlay path is included, protecting the fontconfig/drawtext command contract.
- The real FFmpeg binary successfully extracts a JPEG thumbnail.
- The normal test suite remains portable when FFmpeg is unavailable on a developer host.
- Docker execution does not skip the smoke test because FFmpeg is installed in the image.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_ffmpeg_smoke
python manage.py test --parallel 4
docker compose run --build --rm test
```
