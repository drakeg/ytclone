from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .community_models import CommunityPost, CommunityReply
from .models import Channel


class ChannelCommunityTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="communitycreator", password="password123")
        self.viewer = User.objects.create_user(username="communityviewer", password="password123")
        self.other = User.objects.create_user(username="communityother", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Community Channel", description="Talk with us")

    def test_channel_page_links_to_community(self):
        response = self.client.get(reverse("channel_detail", args=[self.channel.pk]))
        self.assertContains(response, reverse("channel_community", args=[self.channel.pk]))
        self.assertContains(response, "Community")

    def test_community_is_publicly_readable(self):
        CommunityPost.objects.create(channel=self.channel, author=self.creator, body="What should we make next?")
        response = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "What should we make next?")
        self.assertContains(response, "Log in to join the conversation")

    def test_only_channel_owner_can_create_post(self):
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("community_post_create", args=[self.channel.pk]),
            {"kind": CommunityPost.Kind.UPDATE, "body": "Not mine"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(CommunityPost.objects.exists())

        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("community_post_create", args=[self.channel.pk]),
            {"kind": CommunityPost.Kind.UPDATE, "body": "Creator update"},
        )
        self.assertRedirects(response, reverse("channel_community", args=[self.channel.pk]))
        self.assertTrue(CommunityPost.objects.filter(channel=self.channel, body="Creator update").exists())

    def test_authenticated_viewer_can_reply(self):
        post = CommunityPost.objects.create(channel=self.channel, author=self.creator, body="Ask me anything")
        self.client.force_login(self.viewer)
        response = self.client.post(reverse("community_reply_create", args=[post.pk]), {"body": "How did you get started?"})
        self.assertRedirects(response, reverse("channel_community", args=[self.channel.pk]))
        reply = CommunityReply.objects.get(post=post)
        self.assertEqual(reply.author, self.viewer)
        self.assertEqual(reply.body, "How did you get started?")

    def test_authenticated_viewer_can_toggle_like(self):
        post = CommunityPost.objects.create(channel=self.channel, author=self.creator, body="New update")
        self.client.force_login(self.viewer)
        url = reverse("community_post_like", args=[post.pk])
        self.client.post(url)
        self.assertTrue(post.likes.filter(pk=self.viewer.pk).exists())
        self.client.post(url)
        self.assertFalse(post.likes.filter(pk=self.viewer.pk).exists())

    def test_community_page_does_not_show_creator_post_form_to_viewer(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertNotContains(response, "Post to community")

    def test_owner_sees_creator_post_form(self):
        self.client.force_login(self.creator)
        response = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertContains(response, "Post to community")
