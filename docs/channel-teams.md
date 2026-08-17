# Channel Team Roles

## Delivered behavior

Channel owners can delegate upload and video-editing work through an explicit editor role without delegating ownership, analytics, membership administration, deletion, or bulk actions.

## Scope and safeguards

- Owners alone can view and manage a channel's editor list.
- Owners add editors by exact username and can remove them with POST-only actions.
- Owners cannot add themselves, duplicate memberships, or nonexistent users.
- Editors can select assigned channels during upload.
- Editors can edit active videos assigned to their channels, including publication metadata.
- Editors cannot delete videos they did not author, view owner analytics, manage teams, or use owner-scoped bulk actions.
- Cross-channel and forged requests fail safely.
- Existing channel owners and video authors retain their current capabilities.

## Architecture decisions

`ChannelMembership` links one user to one channel with an editor role and a uniqueness constraint. A shared accessible-channel query powers forms and edit authorization. Team administration remains owner-filtered in every mutation.

Migration `0013_channelmembership` adds memberships without changing existing ownership. No dependency, AWS resource, worker, paid service, or external identity system is required.

## Local test plan

```bash
docker compose up --build --detach
docker compose ps
docker compose run --rm test
```

Without Docker:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Focused tests: `python manage.py test video.test_channel_teams`.

Terraform is unaffected. The responsive UI/design-system refresh remains in the roadmap backlog.

## Verification

- Django system checks passed.
- Migration-drift checks reported no changes.
- All 186 tests passed, including 12 focused channel-team tests.
- The migration-leaf regression now covers `0013_channelmembership`.
- Compose configuration validated, and the documented test service runs the same check, drift, and full-suite sequence. The local Docker engine was not accessible from this workspace, so the container invocation remains a local handoff check.

## Out of scope

- Delegated analytics, team administration, deletion, bulk actions, or comment moderation
- Viewer, analyst, and custom roles
- Invitations, email delivery, expiration, and audit logs
