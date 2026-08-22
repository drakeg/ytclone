# Channel Team Roles

## Delivered behavior

Channel owners can delegate upload and video-editing work through an explicit editor role without delegating ownership, analytics, membership administration, deletion, or bulk actions.

## Scope and safeguards

- Owners alone can view and manage a channel's editor list.
- Owners invite editors by exact username and can revoke pending invitations or
  remove active editors with POST-only actions.
- Invitations grant no access until the intended recipient accepts them and
  expire after seven days.
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

## Invitation workflow

The invitation workflow adds an authenticated inbox, recipient-only accept and
decline actions, owner-only revocation, expiration checks, and atomic membership
creation. It uses only the application database and does not send email.

Focused verification:

```bash
python manage.py test video.test_channel_team_invitations
docker compose run --build --rm test
```

Migration `0019_channel_team_invitations` stores the intended recipient, inviter,
unguessable token, state, expiry, and response timestamp. Invitation transitions
are implemented in `video/services/team_invitations.py`; views retain explicit
owner or recipient scoping.

## Invitation verification

- Django system checks passed.
- Migration-drift checks reported no changes.
- All 289 tests passed, including eight focused invitation tests.
- Compose configuration validated. The delivery environment could not access its
  Docker daemon socket, so container execution remains a local handoff check.

## Out of scope

- Delegated analytics, team administration, deletion, bulk actions, or comment moderation
- Viewer, analyst, and custom roles
- Email delivery, reminders, custom roles, invitation extension, and audit logs

## Invitation notifications and activity

The existing notification inbox announces team invitations and links directly to
the private invitation inbox. Navigation shows the number of unexpired pending
invitations. Accepting, declining, or revoking clears the related unread state.
Owners see valid pending invitations separately from a bounded 25-row activity
history, including expired invitations. Email and scheduled delivery remain out
of scope.

Migration `0021_team_invitation_notifications` adds the notification kind. Django
checks, migration-drift checks, and all 301 tests passed directly and through
Docker Compose.
