from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from monetization.models import (
    ChannelMembershipSubscription,
    CreatorMonetizationAccount,
    MembershipTier,
)

from .models import Channel, Comment, Video
from .qa_models import VideoQuestion


class VideoQATests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Q&A Channel", description="Questions welcome")
        self.video = Video.objects.create(
            title="Ask me anything",
            description="A video with questions",
            thumbnail="videos/thumbnails/qa.jpg",
            video_file="videos/files/qa.mp4",
            author=self.creator,
            channel=self.channel,
        )

    def test_question_endpoint_creates_top_level_question(self):
        self.client.force_login(self.viewer)
        response = self.client.post(reverse("ask_video_question", args=[self.video.pk]), {"comment": "How did you start?"})
        self.assertRedirects(response, reverse("video_detail", args=[self.video.pk]))
        comment = Comment.objects.get(comment="How did you start?")
        self.assertIsNone(comment.parent_id)
        self.assertTrue(VideoQuestion.objects.filter(comment=comment).exists())

    def test_existing_comment_endpoint_stays_ordinary(self):
        self.client.force_login(self.viewer)
        self.client.post(reverse("add_comment", args=[self.video.pk]), {"comment": "Great video"})
        comment = Comment.objects.get(comment="Great video")
        self.assertFalse(VideoQuestion.objects.filter(comment=comment).exists())

    def test_only_video_owner_can_feature_direct_visible_reply(self):
        question_comment = Comment.objects.create(video=self.video, author=self.viewer, comment="What camera?")
        question = VideoQuestion.objects.create(comment=question_comment)
        reply = Comment.objects.create(video=self.video, author=self.other, parent=question_comment, comment="Try this one")

        self.client.force_login(self.other)
        denied = self.client.post(reverse("feature_question_answer", args=[reply.pk]))
        self.assertEqual(denied.status_code, 404)

        self.client.force_login(self.creator)
        response = self.client.post(reverse("feature_question_answer", args=[reply.pk]))
        self.assertRedirects(response, reverse("video_detail", args=[self.video.pk]))
        question.refresh_from_db()
        self.assertEqual(question.featured_reply, reply)

        self.client.post(reverse("feature_question_answer", args=[reply.pk]))
        question.refresh_from_db()
        self.assertIsNone(question.featured_reply)

    def test_hidden_reply_cannot_be_featured(self):
        question_comment = Comment.objects.create(video=self.video, author=self.viewer, comment="Question")
        VideoQuestion.objects.create(comment=question_comment)
        reply = Comment.objects.create(video=self.video, author=self.other, parent=question_comment, comment="Hidden answer", is_hidden=True)
        self.client.force_login(self.creator)
        response = self.client.post(reverse("feature_question_answer", args=[reply.pk]))
        self.assertEqual(response.status_code, 404)

    def test_questions_filter_hides_ordinary_comments(self):
        ordinary = Comment.objects.create(video=self.video, author=self.viewer, comment="Ordinary comment")
        question_comment = Comment.objects.create(video=self.video, author=self.viewer, comment="Actual question")
        VideoQuestion.objects.create(comment=question_comment)

        response = self.client.get(reverse("video_detail", args=[self.video.pk]), {"comments": "questions"})
        self.assertNotContains(response, ordinary.comment)
        self.assertContains(response, question_comment.comment)
        self.assertContains(response, "Question")

    def test_supporter_badge_is_opt_in_and_active_only(self):
        account = CreatorMonetizationAccount.objects.create(channel=self.channel)
        tier = MembershipTier.objects.create(
            monetization_account=account,
            name="Supporter",
            price_minor=500,
        )
        membership = ChannelMembershipSubscription.objects.create(
            tier=tier,
            subscriber=self.viewer,
            status=ChannelMembershipSubscription.Status.ACTIVE,
            show_supporter_badge=False,
        )
        question_comment = Comment.objects.create(video=self.video, author=self.viewer, comment="Member question")
        VideoQuestion.objects.create(comment=question_comment)

        response = self.client.get(reverse("video_detail", args=[self.video.pk]))
        self.assertNotContains(response, "Paid member")

        membership.show_supporter_badge = True
        membership.save(update_fields=["show_supporter_badge"])
        response = self.client.get(reverse("video_detail", args=[self.video.pk]))
        self.assertContains(response, "Paid member")

        membership.status = ChannelMembershipSubscription.Status.ENDED
        membership.save(update_fields=["status"])
        response = self.client.get(reverse("video_detail", args=[self.video.pk]))
        self.assertNotContains(response, "Paid member")
