from django.contrib.auth import get_user_model
from django.db import transaction

from video.models import Video
from video.moderation_models import (
    CommunityPostModerationState,
    CommunityReplyModerationState,
    ModerationAuditEvent,
    VideoModerationState,
)

User = get_user_model()


def _reason(value):
    reason = (value or "").strip()
    if not reason:
        raise ValueError("A moderation reason is required.")
    if len(reason) > 1000:
        raise ValueError("Moderation reason must be 1000 characters or fewer.")
    return reason


def _audit(*, actor, action, target_type, target_id, reason):
    return ModerationAuditEvent.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
    )


def set_comment_hidden(*, actor, comment, hidden, reason):
    reason = _reason(reason)
    if comment.is_hidden == hidden:
        return False
    comment.is_hidden = hidden
    comment.save(update_fields=["is_hidden"])
    _audit(
        actor=actor,
        action="comment_hide" if hidden else "comment_restore",
        target_type="comment",
        target_id=comment.pk,
        reason=reason,
    )
    return True


@transaction.atomic
def take_down_video(*, actor, video, reason):
    reason = _reason(reason)
    state, created = VideoModerationState.objects.get_or_create(
        video=video,
        defaults={
            "original_publication_status": video.publication_status,
            "original_publish_at": video.publish_at,
        },
    )
    if created:
        video.publication_status = Video.PublicationStatus.DRAFT
        video.publish_at = None
        video.save(update_fields=["publication_status", "publish_at"])
        _audit(actor=actor, action="video_takedown", target_type="video", target_id=video.pk, reason=reason)
    return created


@transaction.atomic
def restore_video(*, actor, video, reason):
    reason = _reason(reason)
    state = VideoModerationState.objects.filter(video=video).first()
    if state is None:
        return False
    original_status = state.original_publication_status
    original_publish_at = state.original_publish_at
    state.delete()
    video.publication_status = original_status
    video.publish_at = original_publish_at
    video.save(update_fields=["publication_status", "publish_at"])
    _audit(actor=actor, action="video_restore", target_type="video", target_id=video.pk, reason=reason)
    return True


def set_community_post_hidden(*, actor, post, hidden, reason):
    reason = _reason(reason)
    if hidden:
        _, changed = CommunityPostModerationState.objects.get_or_create(post=post)
        action = "community_post_hide"
    else:
        deleted, _ = CommunityPostModerationState.objects.filter(post=post).delete()
        changed = bool(deleted)
        action = "community_post_restore"
    if changed:
        _audit(actor=actor, action=action, target_type="community_post", target_id=post.pk, reason=reason)
    return changed


@transaction.atomic
def set_community_reply_hidden(*, actor, reply, hidden, reason=None, audit=True):
    if audit:
        reason = _reason(reason)
    if hidden:
        _, changed = CommunityReplyModerationState.objects.get_or_create(reply=reply)
        action = "community_reply_hide"
        if changed and reply.post.featured_reply_id == reply.pk:
            reply.post.featured_reply = None
            reply.post.save(update_fields=["featured_reply", "updated_at"])
    else:
        deleted, _ = CommunityReplyModerationState.objects.filter(reply=reply).delete()
        changed = bool(deleted)
        action = "community_reply_restore"
    if changed and audit:
        _audit(actor=actor, action=action, target_type="community_reply", target_id=reply.pk, reason=reason)
    return changed


def set_user_active(*, actor, user, active, reason):
    reason = _reason(reason)
    if user.pk == actor.pk and not active:
        raise ValueError("You cannot suspend your own account.")
    if user.is_superuser and not active:
        raise ValueError("Superuser accounts cannot be suspended here.")
    if user.is_active == active:
        return False
    user.is_active = active
    user.save(update_fields=["is_active"])
    _audit(
        actor=actor,
        action="user_reactivate" if active else "user_suspend",
        target_type="user",
        target_id=user.pk,
        reason=reason,
    )
    return True
