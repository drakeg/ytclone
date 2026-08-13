# Creator Video Management

## Sprint goal

Let creators safely edit and delete their own videos, including moving a video between channels they own.

## Acceptance criteria

- Only the video author can access edit or delete actions; other users receive 404.
- Editable metadata includes title, description, category, thumbnail, and channel.
- Channel choices are restricted to channels owned by the author, including forged-request protection.
- Existing media remains unchanged when replacement files are omitted.
- Deletion accepts POST only, shows an explicit confirmation page, and removes related database records through existing relationships.
- Public video pages expose management actions only to the owner.

## Architecture and testing

A dedicated `VideoEditForm` will reuse upload validation while making media replacement optional. Views will resolve videos by both primary key and `request.user`, preserving the existing ownership boundary. Tests cover authentication, authorization, channel scoping, metadata edits, optional media, deletion confirmation, POST-only deletion, and relationship cleanup.

Run the full suite with `python manage.py check`, `python manage.py makemigrations --check --dry-run`, and `python manage.py test`, or `docker compose run --rm test`.

## Out of scope

- Bulk management
- Drafts and scheduled publishing
- Soft deletion and restore
- Media-object deletion from S3 or local storage
- Channel team roles
