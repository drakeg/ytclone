from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from video.models import ChannelMembership, ChannelTeamInvitation


INVITATION_LIFETIME = timedelta(days=7)


class InvitationError(ValueError):
    pass


@transaction.atomic
def invite_editor(*, channel, invited_by, username):
    invitee = User.objects.filter(username=username).first()
    if invitee is None:
        raise InvitationError("User not found.")
    if invitee.pk == channel.owner_id:
        raise InvitationError("The channel owner is already on the team.")
    if ChannelMembership.objects.filter(channel=channel, user=invitee).exists():
        raise InvitationError("That user is already an editor.")

    now = timezone.now()
    pending = (
        ChannelTeamInvitation.objects.select_for_update()
        .filter(
            channel=channel,
            invitee=invitee,
            status=ChannelTeamInvitation.Status.PENDING,
        )
        .first()
    )
    if pending and pending.expires_at > now:
        raise InvitationError("That user already has a pending invitation.")
    if pending:
        pending.status = ChannelTeamInvitation.Status.EXPIRED
        pending.responded_at = now
        pending.save(update_fields=["status", "responded_at"])

    return ChannelTeamInvitation.objects.create(
        channel=channel,
        invitee=invitee,
        invited_by=invited_by,
        expires_at=now + INVITATION_LIFETIME,
    )


@transaction.atomic
def respond_to_invitation(*, invitation, user, accept):
    invitation = ChannelTeamInvitation.objects.select_for_update().get(
        pk=invitation.pk,
        invitee=user,
        status=ChannelTeamInvitation.Status.PENDING,
    )
    now = timezone.now()
    if invitation.expires_at <= now:
        invitation.status = ChannelTeamInvitation.Status.EXPIRED
        invitation.responded_at = now
        invitation.save(update_fields=["status", "responded_at"])
        return None

    if accept:
        ChannelMembership.objects.get_or_create(
            channel=invitation.channel,
            user=user,
        )
        invitation.status = ChannelTeamInvitation.Status.ACCEPTED
    else:
        invitation.status = ChannelTeamInvitation.Status.DECLINED
    invitation.responded_at = now
    invitation.save(update_fields=["status", "responded_at"])
    return invitation


@transaction.atomic
def revoke_invitation(*, invitation):
    invitation = ChannelTeamInvitation.objects.select_for_update().get(
        pk=invitation.pk,
        status=ChannelTeamInvitation.Status.PENDING,
    )
    invitation.status = ChannelTeamInvitation.Status.REVOKED
    invitation.responded_at = timezone.now()
    invitation.save(update_fields=["status", "responded_at"])
    return invitation


def send_invitation_email(*, invitation, invite_url):
    if not getattr(settings, "TEAM_INVITATION_EMAIL_ENABLED", False):
        return False

    recipient = (invitation.invitee.email or "").strip()
    if not recipient:
        return False

    inviter_name = invitation.invited_by.get_full_name().strip() if invitation.invited_by else ""
    if not inviter_name and invitation.invited_by:
        inviter_name = invitation.invited_by.username
    inviter_name = inviter_name or "A channel owner"
    expiration = timezone.localtime(invitation.expires_at).strftime("%b %-d, %Y at %-I:%M %p %Z")

    subject = f"Invitation to edit {invitation.channel.name} on VideoShare"
    message = (
        f"{inviter_name} invited you to become an editor for "
        f"{invitation.channel.name} on VideoShare.\n\n"
        f"This invitation expires {expiration}.\n\n"
        f"Sign in and review your Team invites here:\n{invite_url}\n\n"
        "If you were not expecting this invitation, you can ignore this email."
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception:
        return False
    return True
