from datetime import timedelta

from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.utils import timezone

from monetization.models import (
    ChannelMembershipSubscription,
    CreatorMonetizationAccount,
    MembershipTier,
)

from .forms import VideoEditForm
from .models import Channel, Video


class MemberEarlyAccessTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.member = User.objects.create_user(username="member", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.channel = Channel.objects.create(
            owner=self.creator,
            name="Early Access Channel",
            description="Members watch first",
        )
        self.account = CreatorMonetizationAccount.objects.create(
            channel=self.channel,
            status=CreatorMonetizationAccount.Status.ACTIVE,
            terms_accepted_at=timezone.now(),
            payouts_enabled=True,
            provider="test",
            provider_account_id="acct_test_early",
        )
        self.tier = MembershipTier.objects.create(
            monetization_account=self.account,
            name="Supporter",
            description="Early access",
            price_minor=500,
        )
        ChannelMembershipSubscription.objects.create(
            tier=self.tier,
            subscriber=self.member,
            status=ChannelMembershipSubscription.Status.ACTIVE,
        )

    def create_video(self, *, public_release_at=None, publication_status=Video.PublicationStatus.PUBLISHED, publish_at=None):
        return Video.objects.create(
            title="Member preview",
            description="Members see this first",
            thumbnail="videos/thumbnails/preview.jpg",
            video_file="videos/files/preview.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=publication_status,
            audience=Video.Audience.MEMBERS_ONLY,
            publish_at=publish_at,
            public_release_at=public_release_at,
        )

    def test_future_public_release_remains_members_only(self):
        video = self.create_video(public_release_at=timezone.now() + timedelta(days=2))

        self.assertTrue(Video.objects.visible_to(self.member).filter(pk=video.pk).exists())
        self.assertFalse(Video.objects.visible_to(self.viewer).filter(pk=video.pk).exists())
        self.assertFalse(Video.objects.visible_to(AnonymousUser()).filter(pk=video.pk).exists())
        self.assertTrue(video.is_early_access)

    def test_past_public_release_is_visible_to_everyone_without_mutation(self):
        video = self.create_video(public_release_at=timezone.now() - timedelta(seconds=1))

        self.assertTrue(Video.objects.visible_to(self.viewer).filter(pk=video.pk).exists())
        self.assertTrue(Video.objects.visible_to(AnonymousUser()).filter(pk=video.pk).exists())
        self.assertTrue(video.has_member_access(AnonymousUser()))
        self.assertFalse(video.is_early_access)

    def test_blank_public_release_remains_permanently_members_only(self):
        video = self.create_video(public_release_at=None)

        self.assertTrue(Video.objects.visible_to(self.member).filter(pk=video.pk).exists())
        self.assertFalse(Video.objects.visible_to(self.viewer).filter(pk=video.pk).exists())

    def test_scheduled_publication_still_controls_when_members_can_first_view(self):
        now = timezone.now()
        video = self.create_video(
            publication_status=Video.PublicationStatus.SCHEDULED,
            publish_at=now + timedelta(hours=2),
            public_release_at=now + timedelta(days=1),
        )

        self.assertFalse(Video.objects.visible_to(self.member).filter(pk=video.pk).exists())
        self.assertTrue(Video.objects.visible_to(self.creator).filter(pk=video.pk).exists())

    def test_everyone_audience_rejects_public_release_time(self):
        video = self.create_video()
        form = VideoEditForm(
            data={
                "title": video.title,
                "description": video.description,
                "channel": self.channel.pk,
                "publication_status": Video.PublicationStatus.PUBLISHED,
                "audience": Video.Audience.EVERYONE,
                "public_release_at": (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"),
                "tags": "",
                "chapters": "",
            },
            instance=video,
            user=self.creator,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("public_release_at", form.errors)

    def test_early_access_public_release_must_be_future(self):
        video = self.create_video()
        form = VideoEditForm(
            data={
                "title": video.title,
                "description": video.description,
                "channel": self.channel.pk,
                "publication_status": Video.PublicationStatus.PUBLISHED,
                "audience": Video.Audience.MEMBERS_ONLY,
                "public_release_at": (timezone.now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M"),
                "tags": "",
                "chapters": "",
            },
            instance=video,
            user=self.creator,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("public_release_at", form.errors)

    def test_scheduled_member_release_must_precede_public_release(self):
        now = timezone.now()
        video = self.create_video()
        form = VideoEditForm(
            data={
                "title": video.title,
                "description": video.description,
                "channel": self.channel.pk,
                "publication_status": Video.PublicationStatus.SCHEDULED,
                "audience": Video.Audience.MEMBERS_ONLY,
                "publish_at": (now + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M"),
                "public_release_at": (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"),
                "tags": "",
                "chapters": "",
            },
            instance=video,
            user=self.creator,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("public_release_at", form.errors)
