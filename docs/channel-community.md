# Channel Communities

## Behavior

Channel owners can publish community posts alongside their videos. Community
content supports text discussions, polls, and highlighted creator Q&A. Viewers
interact through channel-scoped pages, while creator actions remain restricted to
the channel owner.

Poll choices and votes are stored as application data and tested without external
services. Highlighted Q&A allows the creator to surface a selected response while
preserving the surrounding discussion.

## Privacy and permissions

- Community creation and creator moderation are owner-only.
- Interactions require authentication where the corresponding mutation changes
  viewer-owned data.
- Requests are scoped to the channel and related community object rather than
  trusting submitted identifiers.
- Mutations use POST and Django CSRF protection.

## Local verification

Run the full suite because community behavior shares authentication, channels,
and navigation with the rest of the application:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

The equivalent Docker Compose command is:

```bash
docker compose run --build --rm test
```
