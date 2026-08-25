from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from monetization.models import (
    ChannelMembershipSubscription,
    CreatorMonetizationAccount,
    MembershipTier,
)

from .community_models import CommunityPollOption, CommunityPost, CommunityReply
from .models import Channel


class MemberCommunityPerksTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="perkcreator", password="password123")
        self.member = User.objects.create_user(username="perkmember", password="password123")
        self.nonmember = User.objects.create_user(username="perknonmember", password="password123")
        self.channel = Channel.objects.create(
            owner=self.creator,
            name="Perks Channel",
            description="Member perks",
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
        self.subscription = ChannelMembershipSubscription.objects.create(
            tier=self.tier,
            subscriber=self.member,
            status=ChannelMembershipSubscription.Status.ACTIVE,
        )
        self.public_post = CommunityPost.objects.create(
            channel=self.channel,
            author=self.creator,
            body="Public hello",
            audience=CommunityPost.Audience.EVERYONE,
        )
        self.member_post = CommunityPost.objects.create(
            channel=self.channel,
            author=self.creator,
            body="Member hello",
            audience=CommunityPost.Audience.MEMBERS_ONLY,
        )

    def test_public_page_hides_member_post_from_anonymous_and_nonmember(self):
        anonymous = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertContains(anonymous, "Public hello")
        self.assertNotContains(anonymous, "Member hello")

        self.client.force_login(self.nonmember)
        response = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertContains(response, "Public hello")
        self.assertNotContains(response, "Member hello")

    def test_active_member_and_owner_can_see_member_post(self):
        self.client.force_login(self.member)
        member_response = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertContains(member_response, "Member hello")
        self.assertContains(member_response, "Paid members only")

        self.client.force_login(self.creator)
        owner_response = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertContains(owner_response, "Member hello")

    def test_inactive_membership_does_not_grant_access(self):
        self.subscription.status = ChannelMembershipSubscription.Status.PAST_DUE
        self.subscription.save(update_fields=["status"])
        self.client.force_login(self.member)
        response = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertNotContains(response, "Member hello")

    def test_nonmember_direct_interactions_with_member_post_return_404(self):
        poll = CommunityPost.objects.create(
            channel=self.channel,
            author=self.creator,
            body="Member poll",
            kind=CommunityPost.Kind.POLL,
            audience=CommunityPost.Audience.MEMBERS_ONLY,
        )
        option = CommunityPollOption.objects.create(post=poll, text="Yes")
        self.client.force_login(self.nonmember)

        self.assertEqual(
            self.client.post(reverse("community_post_like", args=[self.member_post.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                reverse("community_reply_create", args=[self.member_post.pk]),
                {"body": "Sneaky reply"},
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(reverse("community_poll_vote", args=[option.pk])).status_code,
            404,
        )
        self.assertFalse(CommunityReply.objects.filter(body="Sneaky reply").exists())

    def test_active_member_can_interact_with_member_post(self):
        self.client.force_login(self.member)
        like = self.client.post(reverse("community_post_like", args=[self.member_post.pk]))
        self.assertRedirects(like, reverse("channel_community", args=[self.channel.pk]))
        self.assertTrue(self.member_post.likes.filter(pk=self.member.pk).exists())

        reply = self.client.post(
            reverse("community_reply_create", args=[self.member_post.pk]),
            {"body": "Thanks for the extra update"},
        )
        self.assertRedirects(reply, reverse("channel_community", args=[self.channel.pk]))
        self.assertTrue(
            CommunityReply.objects.filter(
                post=self.member_post,
                author=self.member,
                body="Thanks for the extra update",
            ).exists()
        )

    def test_owner_can_create_members_only_post(self):
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("community_post_create", args=[self.channel.pk]),
            {
                "kind": CommunityPost.Kind.UPDATE,
                "audience": CommunityPost.Audience.MEMBERS_ONLY,
                "body": "Behind the scenes",
            },
        )
        self.assertRedirects(response, reverse("channel_community", args=[self.channel.pk]))
        self.assertTrue(
            CommunityPost.objects.filter(
                channel=self.channel,
                body="Behind the scenes",
                audience=CommunityPost.Audience.MEMBERS_ONLY,
            ).exists()
        )
