from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .community_models import CommunityPollVote, CommunityPost, CommunityReply
from .models import Channel


class CommunityPollAndQATests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="pollcreator", password="password123")
        self.viewer = User.objects.create_user(username="pollviewer", password="password123")
        self.other = User.objects.create_user(username="pollother", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Poll Channel", description="Talk with us")

    def test_creator_can_create_poll_with_options(self):
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("community_post_create", args=[self.channel.pk]),
            {
                "kind": CommunityPost.Kind.POLL,
                "body": "What should we film next?",
                "poll_option_1": "Campground tour",
                "poll_option_2": "Gear review",
                "poll_option_3": "Travel day",
            },
        )
        self.assertRedirects(response, reverse("channel_community", args=[self.channel.pk]))
        post = CommunityPost.objects.get()
        self.assertEqual(post.kind, CommunityPost.Kind.POLL)
        self.assertEqual(list(post.poll_options.values_list("text", flat=True)), ["Campground tour", "Gear review", "Travel day"])

    def test_poll_requires_at_least_two_options(self):
        self.client.force_login(self.creator)
        self.client.post(
            reverse("community_post_create", args=[self.channel.pk]),
            {"kind": CommunityPost.Kind.POLL, "body": "Choose one", "poll_option_1": "Only option"},
        )
        self.assertFalse(CommunityPost.objects.exists())

    def test_viewer_has_one_vote_per_poll_and_can_change_it(self):
        post = CommunityPost.objects.create(channel=self.channel, author=self.creator, kind=CommunityPost.Kind.POLL, body="Pick")
        first = post.poll_options.create(text="A", position=0)
        second = post.poll_options.create(text="B", position=1)
        self.client.force_login(self.viewer)
        self.client.post(reverse("community_poll_vote", args=[first.pk]))
        self.client.post(reverse("community_poll_vote", args=[second.pk]))
        vote = CommunityPollVote.objects.get(post=post, user=self.viewer)
        self.assertEqual(vote.option, second)
        self.assertEqual(CommunityPollVote.objects.filter(post=post, user=self.viewer).count(), 1)

    def test_creator_can_highlight_and_unhighlight_viewer_answer(self):
        post = CommunityPost.objects.create(channel=self.channel, author=self.creator, kind=CommunityPost.Kind.QUESTION, body="Ask me anything")
        reply = CommunityReply.objects.create(post=post, author=self.viewer, body="Here is an answer")
        self.client.force_login(self.creator)
        self.client.post(reverse("community_reply_feature", args=[reply.pk]))
        post.refresh_from_db()
        self.assertEqual(post.featured_reply, reply)
        self.client.post(reverse("community_reply_feature", args=[reply.pk]))
        post.refresh_from_db()
        self.assertIsNone(post.featured_reply)

    def test_non_owner_cannot_highlight_answer(self):
        post = CommunityPost.objects.create(channel=self.channel, author=self.creator, kind=CommunityPost.Kind.QUESTION, body="Question")
        reply = CommunityReply.objects.create(post=post, author=self.viewer, body="Answer")
        self.client.force_login(self.other)
        response = self.client.post(reverse("community_reply_feature", args=[reply.pk]))
        self.assertEqual(response.status_code, 404)
        post.refresh_from_db()
        self.assertIsNone(post.featured_reply)

    def test_community_page_renders_poll_and_highlighted_answer(self):
        post = CommunityPost.objects.create(channel=self.channel, author=self.creator, kind=CommunityPost.Kind.POLL, body="Vote now")
        post.poll_options.create(text="Option A", position=0)
        reply = CommunityReply.objects.create(post=post, author=self.viewer, body="My explanation")
        post.featured_reply = reply
        post.save(update_fields=["featured_reply"])
        response = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertContains(response, "Option A")
        self.assertContains(response, "Creator-highlighted answer")
        self.assertContains(response, "My explanation")
