from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from video.community_models import CommunityPost, CommunityReply
from video.models import Channel, Comment, Video
from video.reporting_models import ContentReport
from video.services.channel_access import available_channels
from video.services.community_access import can_view_community_post


@dataclass(frozen=True)
class ReportTarget:
    target_type: str
    target_id: int
    label: str
    owner_id: int | None
    url: str


def _channel_target(user, target_id):
    channel = available_channels(user).filter(pk=target_id).first()
    if channel is None:
        return None
    return ReportTarget(
        target_type=ContentReport.TargetType.CHANNEL,
        target_id=channel.pk,
        label=channel.name,
        owner_id=channel.owner_id,
        url=reverse("channel_detail", args=[channel.pk]),
    )


def _video_target(user, target_id):
    video = Video.objects.visible_to(user).select_related("channel").filter(pk=target_id).first()
    if video is None:
        return None
    return ReportTarget(
        target_type=ContentReport.TargetType.VIDEO,
        target_id=video.pk,
        label=video.title,
        owner_id=video.author_id,
        url=reverse("video_detail", args=[video.pk]),
    )


def _comment_target(user, target_id):
    comment = Comment.objects.select_related("video").filter(pk=target_id, is_hidden=False).first()
    if comment is None or not Video.objects.visible_to(user).filter(pk=comment.video_id).exists():
        return None
    return ReportTarget(
        target_type=ContentReport.TargetType.COMMENT,
        target_id=comment.pk,
        label=f"Comment on {comment.video.title}",
        owner_id=comment.author_id,
        url=reverse("video_detail", args=[comment.video_id]),
    )


def _community_post_target(user, target_id):
    post = CommunityPost.objects.select_related("channel").filter(pk=target_id).first()
    if (
        post is None
        or not available_channels(user).filter(pk=post.channel_id).exists()
        or not can_view_community_post(user, post)
    ):
        return None
    return ReportTarget(
        target_type=ContentReport.TargetType.COMMUNITY_POST,
        target_id=post.pk,
        label=f"Community post in {post.channel.name}",
        owner_id=post.author_id,
        url=reverse("channel_community", args=[post.channel_id]),
    )


def _community_reply_target(user, target_id):
    reply = CommunityReply.objects.select_related("post__channel").filter(
        pk=target_id,
        moderation_state__isnull=True,
    ).first()
    if (
        reply is None
        or not available_channels(user).filter(pk=reply.post.channel_id).exists()
        or not can_view_community_post(user, reply.post)
    ):
        return None
    return ReportTarget(
        target_type=ContentReport.TargetType.COMMUNITY_REPLY,
        target_id=reply.pk,
        label=f"Community reply in {reply.post.channel.name}",
        owner_id=reply.author_id,
        url=reverse("channel_community", args=[reply.post.channel_id]),
    )


_TARGET_RESOLVERS = {
    ContentReport.TargetType.CHANNEL: _channel_target,
    ContentReport.TargetType.VIDEO: _video_target,
    ContentReport.TargetType.COMMENT: _comment_target,
    ContentReport.TargetType.COMMUNITY_POST: _community_post_target,
    ContentReport.TargetType.COMMUNITY_REPLY: _community_reply_target,
}


def get_reportable_target(user, target_type, target_id):
    resolver = _TARGET_RESOLVERS.get(target_type)
    if resolver is None:
        return None
    target = resolver(user, target_id)
    if target is None:
        return None
    if target.owner_id == getattr(user, "pk", None):
        raise ValueError("You cannot report your own content.")
    return target


def create_report(*, reporter, target, reason, details=""):
    if reason not in ContentReport.Reason.values:
        raise ValueError("Invalid report reason.")
    details = (details or "").strip()
    if len(details) > 1000:
        raise ValueError("Report details must be 1000 characters or fewer.")
    try:
        with transaction.atomic():
            return ContentReport.objects.create(
                reporter=reporter,
                target_type=target.target_type,
                target_id=target.target_id,
                target_label=target.label,
                reason=reason,
                details=details,
            ), True
    except IntegrityError:
        existing = ContentReport.objects.filter(
            reporter=reporter,
            target_type=target.target_type,
            target_id=target.target_id,
            status=ContentReport.Status.OPEN,
        ).first()
        if existing is not None:
            return existing, False
        raise


def report_queue(status):
    selected = status if status in ContentReport.Status.values else ContentReport.Status.OPEN
    return (
        ContentReport.objects.filter(status=selected)
        .select_related("reporter", "reviewed_by")
        .order_by("-created_at", "-pk")
    ), selected


def review_report(*, report, reviewer, action, resolution_note):
    if report.status != ContentReport.Status.OPEN:
        raise ValueError("This report has already been reviewed.")
    if action not in {"resolve", "dismiss"}:
        raise ValueError("Invalid report review action.")
    note = (resolution_note or "").strip()
    if not note:
        raise ValueError("A resolution note is required.")
    if len(note) > 1000:
        raise ValueError("Resolution note must be 1000 characters or fewer.")
    report.status = (
        ContentReport.Status.RESOLVED
        if action == "resolve"
        else ContentReport.Status.DISMISSED
    )
    report.reviewed_by = reviewer
    report.reviewed_at = timezone.now()
    report.resolution_note = note
    report.save(
        update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "resolution_note",
        ]
    )
    return report
