# Draft and Scheduled Publishing

## Delivered behavior

Creators can save drafts, publish immediately, or schedule visibility while unpublished content remains private across public surfaces.

Scheduled videos become visible when their publication time arrives without requiring a background publication worker. Subscriber upload notifications now follow the same low-cost model: due scheduled uploads are detected during ordinary rendered application traffic, and an explicit management command provides a deterministic catch-up path.

## Delivered safeguards

- Existing videos remain published after migration.
- Drafts and future scheduled videos are visible only to their author.
- Scheduled videos become publicly readable when their publication time arrives, without a worker.
- Public search, discovery, channel, category, profile, playlist, and history surfaces exclude unpublished videos.
- Forms require a future time for scheduled status and clear irrelevant timestamps.
- Immediate public uploads notify subscribers once.
- Future scheduled uploads do not notify subscribers before `publish_at`.
- Due scheduled uploads notify subscribers at most once using `upload_notifications_sent_at` as an idempotency marker.
- Draft, unlisted, trashed, and not-yet-due videos are excluded from scheduled notification delivery.
- The channel owner is excluded from their own upload notification.

## Scheduled notification catch-up

Ordinary rendered application traffic processes a small bounded batch of due scheduled uploads. Operators can explicitly catch up a quiet site with:

```bash
python manage.py deliver_scheduled_upload_notifications
```

The default command processes at most 100 due videos. A smaller or larger bounded batch can be selected with `--limit` (1 through 1000):

```bash
python manage.py deliver_scheduled_upload_notifications --limit 250
```

The command is safe to repeat; already-delivered videos are skipped.

## Architecture and testing

`VideoQuerySet.visible_to(user)` remains the centralized visibility policy. `Video` has publication status, an optional publication time, and an upload-notification delivery timestamp. Notification delivery uses the existing in-app `Notification.Kind.UPLOAD` model and transactionally marks each video after creating subscriber notifications.

No email provider, push provider, worker, queue, cron service, AWS resource, paid service, or Terraform change is required.

Migration `0028_video_upload_notifications_sent_at` adds the nullable delivery marker. Existing historical videos are not retroactively notified because only rows still in scheduled status are eligible for due delivery.

## Out of scope

- Email and push delivery
- Per-subscriber notification preferences and digests
- Member-only public-release transition notifications
- Time-zone selection per user
- Approval workflows beyond existing channel teams
- External scheduling infrastructure
