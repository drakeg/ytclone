from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Comment, Video
from .shorts_models import VideoShort


class ShortsBoundedDiscussionTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="bounded-creator", password="password123")
        self.viewer = User.objects.create_user(username="bounded-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Bounded Channel", description="")
        self.video = Video.objects.create(
            title="Bounded Short",
            description="",
            thumbnail="videos/thumbnails/bounded.jpg",
            video_file="videos/files/bounded.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.video)
        self.client.force_login(self.viewer)

    def test_feed_renders_only_three_recent_comments_but_keeps_total_count(self):
        comments = [
            Comment.objects.create(video=self.video, author=self.viewer, comment=f"comment-{index}")
            for index in range(5)
        ]
        response = self.client.get(reverse("shorts_feed"))
        rendered = response.context["shorts"][0]
        self.assertEqual(rendered.shorts_comment_count, 5)
        self.assertEqual(len(rendered.shorts_recent_comments), 3)
        self.assertEqual(
            [comment.pk for comment in rendered.shorts_recent_comments],
            [comments[4].pk, comments[3].pk, comments[2].pk],
        )

    def test_feed_renders_only_two_recent_visible_replies_but_keeps_total_count(self):
        parent = Comment.objects.create(video=self.video, author=self.viewer, comment="parent")
        replies = [
            Comment.objects.create(video=self.video, author=self.creator, parent=parent, comment=f"reply-{index}")
            for index in range(4)
        ]
        Comment.objects.create(video=self.video, author=self.creator, parent=parent, comment="hidden", is_hidden=True)
        response = self.client.get(reverse("shorts_feed"))
        rendered_parent = response.context["shorts"][0].shorts_recent_comments[0]
        self.assertEqual(rendered_parent.shorts_reply_count, 4)
        self.assertEqual(len(rendered_parent.shorts_recent_replies), 2)
        self.assertEqual(
            [reply.pk for reply in rendered_parent.shorts_recent_replies],
            [replies[2].pk, replies[3].pk],
        )
