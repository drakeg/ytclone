# Product Roadmap

## Delivery process

Every sprint follows this checklist:

### Before implementation

- Review the README, architecture, roadmap, AWS, Terraform, and affected feature documentation.
- Update the roadmap with the sprint goal, scope, acceptance criteria, test plan, and out-of-scope work.
- Document the local commands contributors will use to verify the sprint, including both Docker and non-Docker paths.
- Record architecture decisions before code is written.

### During implementation

- Keep the sprint and pull request focused on one concern.
- Add or update tests alongside the implementation.
- Prefer business logic in service modules rather than views.
- Update local test instructions whenever dependencies, configuration, migrations, or validation commands change.

### Before sprint closure

- Update all affected documentation to match delivered behavior and configuration.
- Record new environment variables, migrations, infrastructure, and operational notes.
- Confirm the README contains current Docker and non-Docker instructions for Django system checks, migration-drift checks, and the full unit test suite.
- When Terraform or its workflow is affected, document and run formatting and validation commands.
- Run the documented local checks, record the results in the pull request, and resolve any mismatch between the documentation and the actual commands.
- Update the roadmap with delivered work, deferred work, and next sprint candidates.

A sprint is not closed until its local test instructions are complete and reproducible.

## Completed sprint: Shorts Feed Controller Extraction

Goal: move the remaining inline Shorts feed JavaScript into a namespaced static
controller without changing playback, navigation, sound, social interactions,
sharing, or non-JavaScript fallbacks.

Acceptance criteria:

- The Shorts template contains no inline executable JavaScript.
- A `video/shorts_feed.js` controller owns the existing feed initialization,
  navigation, autoplay, sound, subscription, reaction, comment, and fallback behavior.
- The controller loads only on the Shorts feed and after the feed markup is available.
- Existing extracted reply, reaction-serialization, playback-accessibility, and
  sharing controllers continue to own their specialized enhancements without duplicate requests.
- Standard HTML form fallbacks and all server authorization/visibility behavior remain unchanged.
- Focused regression coverage protects the static path, page scope, initialization,
  and absence of inline executable JavaScript.

Out of scope: UI redesign, behavior changes, CSS extraction, backend changes,
query changes, schema or migrations, dependencies, external services, AWS,
paid services, workers, queues, and Terraform.

Verification before closure:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_shorts_feed_controller
python manage.py test --parallel 4
docker compose run --build --rm test
```

Delivered:

- A literal move of the remaining inline controller to `video/static/video/shorts_feed.js`
- Route-scoped deferred loading through the existing static namespace
- No inline executable JavaScript in the Shorts template
- Preserved feed, playback, sound, navigation, visibility, subscription,
  reaction, comment, and sharing behavior
- Continued ownership by the specialized reply, serialized-reaction,
  playback-accessibility, and sharing controllers
- Four new focused regressions plus updated source-location assertions in affected tests

Verification:

- Django system checks passed and the migration-drift check reported no changes
- All 44 affected Shorts tests passed
- All 536 tests passed directly with four parallel workers
- Docker Compose configuration parsed successfully, and all 536 tests passed
  through `docker compose run --build --rm test`
- No schema, migration, backend, dependency, AWS, paid-service, or Terraform change

## Completed sprint: Private Video Bookmarks

Goal: let signed-in viewers privately save labeled playback moments and return to
them without exposing viewing activity to creators or other users.

Acceptance criteria:

- A signed-in viewer can save a label and the player's current position on videos available through normal visibility rules.
- Saved positions are limited to valid, bounded timestamps and labels are required and length-limited.
- Saving the same position again updates its label instead of creating a duplicate.
- Video pages list only the current viewer's bookmarks in timestamp order and provide accessible seek controls.
- A private bookmarks page lists only the current viewer's bookmarks for videos they can still view.
- Bookmark removal is owner-scoped and POST-only.
- Bookmarks inherit video deletion and visibility behavior and never appear in creator analytics.
- Validation and persistence logic lives in a service module.

Out of scope: shared bookmarks, creator access to viewer bookmarks, notes or
annotations, bookmark folders, automatic highlights, exports, external services,
and Terraform changes.

Verification before closure:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_bookmarks
python manage.py test
docker compose run --build --rm test
```

Delivered:

- Private labels and player-current positions for signed-in viewers
- Exact-position relabeling without duplicate rows
- Required, trimmed 120-character labels and timestamps bounded from zero to 24 hours
- Per-video timestamp ordering with accessible seek and remove controls
- A private Saved moments page that excludes videos no longer visible to the viewer
- Login-required, owner-scoped, POST-only create and remove operations
- Cascade cleanup with permanent video deletion and no creator analytics exposure
- Migration `0023_video_bookmarks` and service-layer validation/persistence

Verification:

- Django checks and migration-drift checks passed directly and in Docker
- All 316 tests passed directly and through `docker compose run --build --rm test`
- No dependency, environment variable, AWS resource, paid service, or Terraform change

## Completed sprint: Video Chapters

Goal: let authorized creators define timestamped video sections and let viewers
jump to them from the existing player.

Acceptance criteria:

- Upload and edit forms accept one chapter per line as `MM:SS Title` or `HH:MM:SS Title`.
- A chapter list is optional, limited to 50 entries, strictly increasing, and must start at zero.
- Empty chapter text removes existing chapters only after a valid form submission.
- Video owners and assigned editors retain their existing edit permissions; no new role is introduced.
- Visible video pages render ordered, keyboard-accessible chapter controls that seek the player.
- Chapters inherit all existing video visibility, unlisted-link, member-only, and deletion behavior.
- Parsing and replacement logic lives in a service module.

Out of scope: automatic chapter generation, transcripts, waveform analysis,
per-chapter analytics, thumbnail sprites, and external services.

Verification before closure:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_chapters
python manage.py test
docker compose run --build --rm test
```

Delivered:

- Optional chapter entry on upload and edit forms
- `MM:SS` and `HH:MM:SS` parsing with first-at-zero, ordering, title, and count validation
- Atomic chapter replacement that preserves existing data after invalid submissions
- Existing owner/editor authorization with no expanded role permissions
- Ordered, accessible player controls that seek and resume playback
- Visibility inheritance and cascade behavior through the parent video
- Migration `0022_video_chapters` and service-layer parsing/replacement

Verification:

- Django checks and migration-drift checks passed directly and in Docker
- All 308 tests passed directly and through `docker compose run --build --rm test`

## Completed sprint: Team Invitation Notifications and Activity

Goal: make consent-based editor invitations discoverable and auditable using the
existing in-app notification system, without adding email infrastructure.

Acceptance criteria:

- Creating an invitation creates one private notification for its intended recipient.
- Notification links lead to the recipient's private invitation inbox.
- Navigation shows the recipient's unexpired pending invitation count.
- Accepting, declining, or owner-revoking an invitation clears its unread notification.
- Owners see pending invitations separately from a bounded recent activity history.
- Expired invitations appear as expired without granting access.
- All notification, invitation, and channel data remains user/owner scoped.

Out of scope: email delivery, scheduled reminders, push notifications, external
providers, workers, custom roles, and permanent audit-log retention.

Verification before closure:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_channel_team_notifications
python manage.py test
docker compose run --build --rm test
```

Delivered:

- One private in-app notification per successfully created invitation
- Direct notification links to the recipient's invitation inbox
- Unexpired pending invitation counts in authenticated navigation
- Automatic unread clearing after accept, decline, or owner revocation
- Separate owner views for valid pending invitations and 25 recent activity rows
- Expired invitation presentation without editor access
- Migration `0021_team_invitation_notifications`

Verification:

- Django checks and migration-drift checks passed directly and in Docker
- All 301 tests passed directly and through `docker compose run --build --rm test`

## Completed sprint: Creator Watch-Time Analytics

Goal: collect bounded playback heartbeats and expose private, aggregate watch-time
metrics without treating resume position as elapsed viewing.

Acceptance criteria:

- Record idempotent heartbeats only for visible videos, capped at 15 seconds each.
- Support authenticated and anonymous playback through privacy-preserving session identifiers.
- Reject malformed durations, positions, deltas, identifiers, and inaccessible videos.
- Show creators total watch hours, average view duration, average percentage viewed,
  and 25/50/75/100% retention reach for each owned video.
- Support lifetime and trailing 28-day reporting without exposing viewer-level data.
- Keep telemetry and aggregation in service modules and require no external service.

Out of scope: second-by-second graphs, geography, traffic sources, exports,
background rollups, warehouses, advertising analytics, or Terraform changes.

Verification before closure:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_watch_time_analytics
python manage.py test
docker compose run --build --rm test
```

Delivered:

- Idempotent playback heartbeats capped at 15 seconds
- Authenticated attribution and hashed anonymous session identifiers
- Active-player and visible-tab browser safeguards with seek resets
- Creator-only total watch hours, average duration, average percentage viewed,
  and quarter-mark retention reach per video
- Lifetime and trailing 28-day filters
- Migration `0020_video_watch_events` and service-layer aggregation

Verification:

- Django checks and migration-drift checks passed directly and in Docker
- All 295 tests passed directly and through `docker compose run --build --rm test`

## Completed sprint: Channel Team Invitations

Goal: replace immediate editor assignment with an explicit, expiring invitation
that the intended user can accept or decline.

Scope and acceptance criteria:

- Owners invite an existing user by exact username instead of granting access immediately.
- Pending invitations expire after seven days and never grant editor permissions.
- Only the intended recipient can view, accept, or decline an invitation.
- Acceptance creates one editor membership atomically; decline and expiration do not.
- Owners can revoke their channel's pending invitations with POST-only actions.
- Existing editors and their bounded upload/edit permissions remain unchanged.
- Local Docker and non-Docker verification instructions remain reproducible.

Out of scope:

- Email delivery, reminders, custom roles, and invitation extension
- Delegated analytics, deletion, monetization, moderation, or team administration
- Audit-log retention beyond invitation state and timestamps
- New AWS resources, workers, queues, or paid services

Local verification before closure:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_channel_team_invitations
python manage.py test
```

The equivalent containerized verification is:

```bash
docker compose run --build --rm test
```

Delivered:

- Owner-created invitations for existing users by exact username
- Seven-day expiration with no permissions before acceptance
- Private invitation inbox with recipient-only accept and decline actions
- Atomic membership creation and replay-safe response handling
- Owner-only POST revocation and unchanged active-editor removal
- Migration `0019_channel_team_invitations`
- Invitation business logic isolated in `video/services/team_invitations.py`

Verification:

- Django system checks passed
- Migration-drift checks reported no changes
- All 289 tests passed, including eight focused invitation regressions
- Docker Compose configuration parsed successfully
- Container execution remains available through the documented command; the
  delivery environment could not access its Docker daemon socket

## Completed sprint: Post-Expansion Hardening

Goal: preserve the recently delivered onboarding, monetization, memberships, and
community features while tightening access revocation, payment accounting, and
core navigation behavior.

Scope and acceptance criteria:

- Bind unlisted-media session grants to the current share token so rotating a
  link immediately revokes previously granted direct-media access.
- Account for Stripe's cumulative partial-refund values incrementally so total
  refunds and fee reversals never exceed the provider-reported amount.
- Prevent a viewer from starting a second Stripe membership for the same channel
  while another membership is active.
- Make logout a CSRF-protected POST action and return users to the working home
  route after logout.
- Remove unused browser code with invalid integrity metadata.
- Bring the README, roadmap, and feature documentation up to date with the
  recently delivered product areas.

Out of scope:

- Live Stripe mode, automatic membership-tier switching, and production payouts
- A visual redesign or recommendation-system changes
- New AWS services or Terraform resources

Local verification before closure:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

The equivalent containerized verification is:

```bash
docker compose run --build --rm test
```

Terraform is not in scope. If implementation unexpectedly changes `terraform/`,
also run the formatting and validation commands documented in the README.

Delivered:

- Share-token-bound media grants with immediate rotation revocation
- Incremental accounting for cumulative Stripe partial refunds and fee reversals
- Duplicate active Stripe membership prevention at checkout and webhook boundaries
- CSRF-protected POST logout with a working homepage redirect
- Removal of unused browser code with invalid integrity metadata
- Isolated uploaded-media tests that remain reproducible across repeated local runs
- Catch-up documentation for onboarding, monetization, memberships, and communities

Verification:

- Django system checks passed
- Migration-drift checks reported no changes
- All 281 tests passed, including the new focused regressions
- Docker Compose configuration parsed successfully
- `docker compose run --build --rm test` remains the documented container path;
  the delivery environment could not access its Docker daemon socket

## Completed foundation

- Environment-based secrets and production security settings
- Django 6.1 dependency baseline
- Docker development and Gunicorn production runtime
- CI for Django and Terraform validation
- Authentication and authorization hardening
- Mutually exclusive reactions
- Session-based view counting
- Upload validation and configurable limits
- Optional private S3 media storage
- Terraform modules for private media storage and AWS budget alerts
- Playlists with public, unlisted, and private visibility
- Private watch history with removal and clear-all controls
- Grouped Search and Discovery across videos, channels, and visible playlists
- Homepage Discovery with newest, most viewed, most liked, recently watched, and public playlist sections
- Continue Watching with private playback progress, automatic resume, and containerized test execution
- Private Creator Analytics for lifetime uploads, views, reactions, and unique subscribers
- Private in-app notifications for comments, reactions, subscriptions, and unread state
- Explicit video-to-channel publishing and subscriber new-upload notifications
- Owner-only per-channel analytics with isolated lifetime metrics
- Owner-only video metadata editing, channel moves, and confirmed deletion
- Draft, immediate, and scheduled publication with centralized visibility
- Unlisted videos with hard-to-guess, revocable direct links

## Completed sprint: Search and Discovery

Delivered:

- Video matching by title, description, category, and creator username
- Channel matching by name and description
- Playlist matching by name and description
- Grouped result sections for videos, channels, and playlists
- Video sorting by relevance, newest, oldest, most viewed, and most liked
- Private playlists excluded from search
- Public playlists searchable by anyone
- Owners able to find their own unlisted playlists without exposing them to other users
- Search business logic isolated in `video/services/search.py`
- Regression tests for matching, visibility, sorting, invalid sort values, and blank queries

Deferred:

- Search suggestions and autocomplete
- Search history
- PostgreSQL full-text search
- Elasticsearch or OpenSearch
- Semantic or embedding search
- Duration, resolution, and upload-date filters

## Completed sprint: Homepage Discovery

Goal: replace the homepage's chronological list with bounded discovery sections built from the search, reaction, playlist, and history foundations.

- Newest videos
- Most viewed videos
- Most liked videos
- Recently watched videos for authenticated users
- Recently updated public playlists

Delivered:

- Bounded sections for newest, most viewed, and most liked videos
- Private, per-user recently watched videos for authenticated users
- Recently updated public playlists with video counts
- Privacy enforcement that excludes private and unlisted playlists
- Clear empty states and an anonymous homepage without history content
- Discovery query logic isolated in `video/services/discovery.py`
- Regression tests for ordering, limits, privacy, history isolation, anonymous behavior, and empty data

Deferred:

- Personalized recommendations beyond watch history
- Playback-position tracking and Continue Watching
- Trending time windows and ranking decay
- Featured-channel curation
- Infinite scrolling and homepage pagination
- Background workers, caches, or machine-learning recommendations

## Completed sprint: Continue Watching

Add private playback-position tracking, resumable video playback, and an unfinished-video homepage section. Also add a one-command Docker Compose test runner for the complete Django verification suite.

Delivered:

- Authenticated playback progress saved to the existing private watch-history record
- Automatic resume on the video detail page
- Continue Watching homepage section ordered by recent activity
- Completed and near-complete videos excluded from Continue Watching
- Safe endpoint validation, clamping, CSRF protection, and per-user isolation
- Migration `0005_watchhistory_playback_progress` with backward-compatible defaults
- One-command containerized verification through `docker compose run --rm test`
- Regression tests for authorization, validation, isolation, resume behavior, filtering, ordering, and homepage visibility

Deferred:

- Real-time synchronization between simultaneous players
- Chapters and bookmarks
- Playback analytics and creator reporting
- Recommendation ranking based on completion
- Background workers, caches, and external event pipelines

## Completed sprint: Creator Analytics

Add a private creator dashboard for lifetime upload, view, reaction, and unique subscriber metrics using existing application data.

Delivered:

- Login-protected creator dashboard with no user-selectable analytics target
- Lifetime upload, view, like, dislike, and unique subscriber totals
- Subscriber deduplication across every channel owned by the creator
- Deterministically ranked video performance table
- Useful zero metrics and empty state for new creators
- Analytics aggregation isolated in `video/services/analytics.py`
- Regression tests for authentication, isolation, totals, deduplication, ordering, rendering, and navigation

Deferred:

- Historical trends, date comparisons, and charts
- Watch time, retention, traffic sources, and geography
- Per-channel video analytics until videos explicitly belong to channels
- CSV export and scheduled reports
- Background aggregation and third-party analytics services

## Completed sprint: In-App Notifications

Add private, database-backed notifications for comments, reactions, and subscriptions, with an unread inbox and no external delivery infrastructure.

Delivered:

- Database-backed notifications for new comments, likes, dislikes, and subscriptions
- Self-actions, removed reactions, and unsubscribes kept silent
- Private newest-first inbox with empty state and direct target links
- Per-notification and mark-all read actions restricted to POST
- Cross-user read protection and recipient-scoped unread navigation badge
- Notification creation isolated in `video/services/notifications.py`
- Migration `0006_notification` and regression tests for events, privacy, unread state, and mutations

Deferred:

- Email, browser push, SMS, and mobile push
- Real-time sockets and polling
- New-upload notifications until videos explicitly belong to channels
- Notification preferences and digest schedules
- Background workers and external message brokers

## Completed sprint: Video Channel Ownership

Delivered:

- Nullable explicit channel relationship for backward compatibility
- Safe data migration to each author's oldest existing channel
- Upload form restricted to authenticated creator-owned channels
- Forged cross-owner channel submissions rejected
- Channel pages isolated to explicitly assigned videos
- Private new-upload notifications for channel subscribers
- Regression coverage for ownership, migration compatibility, isolation, and notifications

Deferred:

- Moving videos between channels after upload
- Multiple channels per video
- Channel roles and team management
- Historical per-channel charts
- External notification delivery

## Completed sprint: Per-Channel Analytics

Delivered:

- Owner-only channel analytics route with anonymous login redirect
- Cross-owner requests hidden with 404
- Channel-scoped upload, view, reaction, and subscriber totals
- Deterministic channel video performance table
- Legacy null-channel and other-channel videos excluded
- Owner-only analytics link and useful empty state
- Aggregation isolated in the existing analytics service

Deferred:

- Historical trends and date ranges
- Watch time and retention
- CSV exports
- Channel teams and delegated access
- Background aggregation and third-party analytics

## Completed sprint: Creator Video Management

Delivered:

- Owner-only edit and delete routes with cross-user 404 protection
- Metadata editing and moves between creator-owned channels
- Forged foreign-channel submissions rejected
- Existing thumbnail and video files preserved when replacements are omitted
- Owner-only management actions on public video pages
- Explicit deletion confirmation followed by POST mutation
- Related comments, history, playlist entries, and notifications removed through model relationships

Deferred:

- Bulk management
- Drafts and scheduled publishing
- Soft deletion and restore
- Media-object deletion from S3 or local storage
- Channel team roles

## Completed sprint: Draft and Scheduled Publishing

Delivered:

- Draft, scheduled, and published states with backward-compatible defaults
- Dynamic scheduled visibility without background workers
- Centralized `visible_to` policy for owners and public viewers
- Privacy enforcement across detail, discovery, search, channel, category, profile, playlist, and history surfaces
- Future-time validation and irrelevant timestamp cleanup
- Immediate-public upload notifications retained
- Regression coverage for defaults, validation, privacy, due schedules, and owner access

Deferred:

- Background publication jobs and scheduled notification delivery
- Unlisted videos and share tokens
- Per-user time-zone selection
- Approval workflows and channel teams

## Completed sprint: Unlisted Video Sharing

Delivered:

- Unlisted publication state with unique UUID share tokens
- Anonymous direct viewing through valid share links
- Owner-only access through ordinary video URLs
- POST-only owner token rotation with immediate revocation
- Draft and scheduled videos rejected by share routes
- Unlisted videos excluded from every public discovery surface
- Owner-only share controls and regression coverage

Deferred:

- Password-protected links
- Link expiration dates and access limits
- Viewer identity and access auditing
- Share-link notifications
- Signed CDN URLs beyond existing media behavior

## Completed sprint: Creator Publication Management

Goal: give creators a private, filterable video library with safe bulk visibility actions.

Delivered:

- Owner-only creator video library
- Filters for all publication states
- POST-only bulk transitions to draft, unlisted, or published
- Strict ownership scoping for submitted video IDs
- Timestamp cleanup for states that do not use scheduling
- Empty-state, invalid-input, and privacy regression coverage
- Docker and non-Docker verification instructions

Out of scope:

- Bulk scheduling, which requires a per-video future timestamp
- Bulk metadata or channel changes
- Publication-transition notifications
- Background jobs, approval workflows, and channel teams

Verification:

- Django system checks passed
- Migration-drift checks reported no changes
- All 123 tests passed, including 11 focused publication-management tests
- Docker Compose configuration and the container test script validated
- Docker execution remains available through `docker compose run --rm test`; the daemon was unavailable on the delivery host

## Completed sprint: Creator Video Trash and Restore

Goal: replace immediate destructive deletion with private recovery, enforced retention, and safe permanent-deletion boundaries.

Delivered:

- Owner-only soft deletion and private trash
- Exclusion from every viewer and creator surface
- Thirty-day minimum retention
- POST-only restore to draft
- Confirmed permanent database deletion after retention
- Relationship retention until permanent deletion
- Explicit media preservation and deferred cleanup
- Docker and non-Docker regression instructions

Out of scope:

- Automatic purge workers
- Local or S3 media deletion
- Bulk trash operations
- Administrative retention overrides

Verification:

- Django system checks passed
- Migration-drift checks reported no changes
- All 134 tests passed, including 11 focused trash tests
- Docker Compose configuration, the container test script, and Python compilation validated
- Docker execution remains available through `docker compose run --rm test`; the daemon was unavailable on the delivery host

## Completed sprint: Creator Comment Moderation

Goal: add reversible owner-only comment review and a fully documented Docker Compose application workflow.

Delivered:

- Private creator comment queue
- All, visible, and hidden filters
- POST-only bulk hide and restore
- Strict active-video ownership scoping
- Public exclusion without destructive deletion
- Default Compose startup isolated from the test runner
- Container health, status, logs, tests, and shutdown instructions
- Docker and non-Docker regression coverage

Out of scope:

- Permanent bulk deletion
- Automated classification and keyword filters
- Moderator roles, appeals, and external services

Verification:

- Django system checks passed
- Migration-drift checks reported no changes
- All 150 tests passed, including 13 focused comment-moderation tests and three migration/root-route regressions
- A fresh SQLite database successfully applied the complete `video` migration chain and exposed the video table
- Default Compose configuration exposes only the long-lived web service
- The test profile, health check, shell scripts, and Python compilation validated
- Full startup and containerized tests remain documented; the Docker daemon was unavailable on the delivery host

## Completed sprint: Viewer Comment Ownership

Goal: let viewers edit and delete their own comments while preserving creator moderation and video visibility rules.

Delivered:

- Author-only comment editing
- Hidden-state preservation during edits
- Confirmed, POST-only author deletion
- Centralized active-video visibility enforcement
- Empty-input and forged-access safeguards
- Owner-only controls on visible comments
- Docker and non-Docker regression instructions

Out of scope:

- Comment version history and undo
- Soft deletion for viewer comments
- Replies, threads, mentions, and rich text
- Creator editing of viewer-authored comments

Verification:

- Django system checks passed
- Migration-drift checks reported no changes
- All 161 tests passed, including 11 focused comment-ownership tests
- Compose configuration, Docker shell scripts, and Python compilation validated
- Local Compose application startup was confirmed after the migration-baseline hotfix

## Completed sprint: Threaded Comment Replies

Goal: add one-level conversations with parent-scoped moderation, author ownership, and deduplicated notifications.

Delivered:

- One-level replies to visible top-level comments
- Same-video and visibility enforcement
- Parent-thread and individual-reply moderation behavior
- Existing author edit/delete compatibility
- Parent-author reply notifications without creator duplicates
- Cascade deletion with explicit confirmation
- Docker and non-Docker regression instructions

Out of scope:

- Arbitrarily deep nesting
- Reply pagination, mentions, real-time updates, and rich text

Verification:

- Django system checks passed
- Migration-drift checks reported no changes
- All 174 tests passed, including 13 focused reply tests
- Migration-leaf regression updated through `0012`
- Compose configuration, Docker shell scripts, and Python compilation validated

## Completed sprint: Channel Team Roles

Goal: add owner-managed editors for delegated uploads and video editing.

Delivered:

- Owner-only editor administration
- Assigned-channel uploads
- Editor access to active channel-video editing
- Explicit exclusion from analytics, deletion, teams, moderation, and bulk actions
- Ownership and forged-request regression coverage
- Docker and non-Docker test instructions

Out of scope:

- Delegated analytics, team administration, deletion, bulk actions, and comment moderation
- Viewer, analyst, and custom roles
- Invitations, email delivery, membership expiration, and activity audit logs

Verification:

- Django system checks passed
- Migration-drift checks reported no changes
- All 186 tests passed, including 12 focused channel-team tests
- Migration-leaf regression updated through `0013`
- Compose configuration validated; the local Docker engine was inaccessible from this workspace, so container execution remains a local handoff check

## Later candidates

- Optional channel-team invitation email delivery and scheduled reminders
- Low-cost AWS application hosting and deployment

## Completed product expansion

Delivered after the interface sprint:

- Self-service registration, editable profiles, and creator-channel onboarding
- Configurable Compose host port and documented local startup workflow
- Drag-and-drop uploads with optional categories and thumbnails
- Role-aware viewer and creator navigation
- Sandbox creator monetization, tips, tiers, and members-only videos
- Stripe test-mode checkout, webhooks, cancellation lifecycle, refunds, and ledger reporting
- Channel community posts, polls, and highlighted creator Q&A

The current hardening sprint follows this expansion and closes its documentation
gap while adding regression coverage around the highest-risk boundaries.

## Completed sprint: Interface and Design System

Goal: replace prototype styling with an original, polished, responsive video-platform interface.

Delivered:

- Cohesive color, type, spacing, elevation, and component tokens
- Responsive header, navigation drawer, search, and creator actions
- Redesigned video cards, discovery sections, and playback detail
- Consistent channels, profiles, playlists, forms, tables, analytics, comments, notifications, and empty states
- Keyboard focus, contrast, semantic landmarks, and reduced-motion safeguards
- Docker and non-Docker regression instructions plus desktop/mobile visual verification

Out of scope:

- YouTube branding or pixel-level imitation
- Product behavior, permissions, recommendation logic, or infrastructure changes
- Front-end frameworks, paid services, and user-selectable themes

Verification:

- Django system checks and migration-drift checks passed
- All 189 tests passed, including three focused interface-shell tests
- Compose configuration, Docker shell scripts, and Python compilation validated
- Homepage verified at 1440 × 900 and 390 × 844 without overflow or browser errors
- Video detail verified at desktop and phone widths with responsive playback, creator, and comment layouts
- Local Docker engine access remained unavailable, so container execution remains a local handoff check
