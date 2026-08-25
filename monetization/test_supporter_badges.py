from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from video.community_models import CommunityPost, CommunityReply
from video.models import Channel

from .models import (
    ChannelMembershipSubscription,
    CreatorMonetizationAccount,
    MembershipTier,
)


class SupporterBadgeTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="badgecreator", password="password123")
        self.member = User.objects.create_user(username="badgemember", password="password123")
        self.other = User.objects.create_user(username="badgeother", password="password123")
        self.channel = Channel.objects.create(
            owner=self.creator,
            name="Badge Channel",
            description="Recognition",
        )
        self.account = CreatorMonetizationAccount.objects.create(
            channel=self.channel,
            status=CreatorMonetizationAccount.Status.ACTIVE,
            payouts_enabled=True,
            terms_accepted_at=timezone.now(),
        )
        self.tier = MembershipTier.objects.create(
            monetization_account=self.account,
            name="Supporter",
            price_minor=500,
        )
        self.membership = ChannelMembershipSubscription.objects.create(
            tier=self.tier,
            subscriber=self.member,
            status=ChannelMembershipSubscription.Status.ACTIVE,
        )
        self.post = CommunityPost.objects.create(
            channel=self.channel,
            author=self.creator,
            body="Say hello",
        )
        CommunityReply.objects.create(
            post=self.post,
            author=self.member,
            body="Hello from a supporter",
        )

    def test_badge_is_private_by_default(self):
        self.assertFalse(self.membership.show_supporter_badge)
        response = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertContains(response, "Hello from a supporter")
        self.assertNotContains(response, "Paid member")

    def test_member_can_opt_in_and_out_from_billing(self):
        self.client.force_login(self.member)
        url = reverse("monetization:toggle_supporter_badge", args=[self.membership.pk])

        response = self.client.post(url)
        self.assertRedirects(response, reverse("monetization:membership_billing"))
        self.membership.refresh_from_db()
        self.assertTrue(self.membership.show_supporter_badge)

        community = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertContains(community, "Paid member")

        self.client.post(url)
        self.membership.refresh_from_db()
        self.assertFalse(self.membership.show_supporter_badge)

    def test_other_user_cannot_change_badge_preference(self):
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("monetization:toggle_supporter_badge", args=[self.membership.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.membership.refresh_from_db()
        self.assertFalse(self.membership.show_supporter_badge)

    def test_inactive_membership_never_displays_badge(self):
        self.membership.show_supporter_badge = True
        self.membership.status = ChannelMembershipSubscription.Status.ENDED
        self.membership.save(update_fields=["show_supporter_badge", "status"])

        response = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertContains(response, "Hello from a supporter")
        self.assertNotContains(response, "Paid member")

        self.client.force_login(self.member)
        toggle = self.client.post(
            reverse("monetization:toggle_supporter_badge", args=[self.membership.pk])
        )
        self.assertEqual(toggle.status_code, 404)
