# Post-Expansion Hardening Sprint

## Purpose

This sprint follows the registration, creator onboarding, monetization,
membership, and channel-community expansion. It is intentionally limited to
correctness, privacy, accounting, navigation, and documentation hardening.

## Required behavior

- Rotating an unlisted video's share link revokes existing session-based access
  to its protected media file.
- Repeated Stripe partial-refund events use the provider's cumulative refunded
  amount without double-counting earlier refund events.
- A viewer cannot create parallel active Stripe memberships for one channel.
  Tier changes require the existing membership to be canceled first.
- Logout uses a CSRF-protected POST request and redirects to the homepage.
- Documentation accurately describes current capabilities and local testing.

## Verification

Without Docker, from an activated environment with dependencies installed:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

With Docker Compose:

```bash
docker compose run --build --rm test
```

Focused tests may be run during development, but sprint closure requires the
full command for the chosen environment. The pull request records which paths
were executed and any host limitation that prevented Docker execution.

## Delivery results

- `python manage.py check`: passed
- `python manage.py makemigrations --check --dry-run`: no changes detected
- `python manage.py test`: all 281 tests passed
- `docker compose config --quiet`: passed
- `docker compose run --build --rm test`: not executable on the delivery host
  because its Docker daemon socket was inaccessible; the command remains the
  required local container verification path

No migrations, Terraform resources, paid services, or live Stripe behavior were
added by this sprint.
