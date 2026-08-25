# Member Community Perks Sprint

## Goal

Connect paid memberships to the channel community in a way that gives supporters meaningful optional perks without making the free community worse.

## Scope

- Let channel owners mark community updates, questions, and polls as either **Everyone** or **Paid members only**.
- Keep normal public community posts fully available to all viewers.
- Enforce member-only visibility and interaction server-side for posts, replies, likes, and poll votes.
- Let an active paid member opt in to a small supporter badge on their community replies for that channel.
- Default supporter recognition to **off**; paying never automatically exposes membership status publicly.
- Give members a simple toggle from their paid-memberships area.
- Treat channel owners as authorized to see and manage their own member-only community posts.
- Keep all membership entitlement checks in service helpers rather than templates alone.

## Acceptance criteria

- Anonymous and non-member viewers cannot see member-only community posts.
- Active paid members can see and interact with member-only posts.
- Past-due, canceled, and ended memberships do not grant member-only community access.
- Channel owners can create and view member-only posts.
- Direct POST attempts to like, reply, or vote on inaccessible member-only posts return not found rather than leaking existence.
- Supporter badges appear only for active members who explicitly opt in for that channel.
- Opting out removes the badge without affecting paid access.
- Free community posts and interactions continue to work unchanged.
- No live-payment, AWS, external-service, or paid-infrastructure change is introduced.

## Out of scope

- Tier-specific posts or per-tier entitlements
- Public supporter leaderboards
- Spending-based badge levels
- Gifting memberships
- Member-only live chat
- Email/push notifications for community posts
- Terraform changes

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_member_community_perks monetization.test_supporter_badges
python manage.py test
docker compose run --build --rm test
```
