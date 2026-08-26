# Member Early-Access Sprint

## Goal

Let creators reward paid members with early access to a video that automatically becomes available to everyone at a scheduled time, without requiring a worker, cron job, external service, or live payment change.

## Product model

Early access is an extension of the existing paid-members-only audience. A video can remain permanently members-only, or it can have an optional future public-release timestamp. Before that timestamp, normal active paid-membership authorization applies. At or after the timestamp, normal public visibility applies automatically from request-time visibility rules.

## Acceptance criteria

- Upload/edit forms allow a creator to set an optional public-release time when audience is Paid members only.
- A public-release time must be in the future when saved and is invalid for Everyone-audience videos.
- Before the public-release time, only the creator/channel owner and active paid members can view/discover the video.
- At or after the public-release time, the same video becomes visible to ordinary viewers without a background job or mutation.
- Permanent members-only videos continue working by leaving the public-release time blank.
- Discovery/search/category/channel/hashtag surfaces inherit the behavior through `Video.objects.visible_to(user)`.
- Video detail and creator management surfaces clearly label early-access state and public-release time.
- Existing scheduled publication remains independent: publication timing controls when the video exists for its intended audience; early-access timing controls when a members-only audience opens to everyone.
- No live Stripe changes, external service, worker, queue, AWS resource, paid infrastructure, or Terraform change.

## Out of scope

- Tier-specific early access
- Email/push notifications at public release
- Premiere/live chat
- Automatic social posting
- Changes to membership pricing or billing

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_member_early_access
python manage.py test
docker compose run --build --rm test
```
