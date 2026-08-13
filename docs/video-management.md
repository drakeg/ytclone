# Creator Video Management

## Delivered behavior

Creators can safely edit and delete their own videos, including moving a video between channels they own.

## Delivered safeguards

- Only the video author can access edit or delete actions; other users receive 404.
- Editable metadata includes title, description, category, thumbnail, and channel.
- Channel choices are restricted to channels owned by the author, including forged-request protection.
- Existing media remains unchanged when replacement files are omitted.
- Deletion accepts POST only, shows an explicit confirmation page, and removes related database records through existing relationships.
- Public video pages expose management actions only to the owner.

## Architecture and testing

A dedicated `VideoEditForm` reuses upload validation while making media replacement optional. Views resolve videos by both primary key and `request.user`, preserving the existing ownership boundary. Deletion uses Django's existing cascades for related database records; stored media-object deletion remains deliberately out of scope.

The sprint-close non-Docker run passed Django checks, reported no migration drift, and completed all 98 tests successfully. Docker is unavailable on the delivery host; run `docker compose run --rm test` on a Docker-enabled machine.

No migrations, dependencies, environment variables, AWS resources, or external services are added.

## Out of scope

- Bulk management
- Drafts and scheduled publishing
- Soft deletion and restore
- Media-object deletion from S3 or local storage
- Channel team roles
