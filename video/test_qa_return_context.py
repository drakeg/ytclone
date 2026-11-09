from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Video
from .qa_models import VideoQuestion


class QAReturnContextTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="qa-context-creator",
            password="password123",
        )
        self.viewer = User.objects.create_user(
            username="qa-context-viewer",
            password="password123",
        )
        self.replier = User.objects.create_user(
            username="qa-context-replier",
            password="password123",
        )
        self.video = Video.objects.create(
            title="Q&A context video",
            description="Q&A return context coverage",
            thumbnail="videos/qa-context.jpg",
            video_file="videos/qa-context.mp4",
            author=self.creator,
        )

    def create_question_with_reply(self):
        question_comment = Comment.objects.create(
            video=self.video,
            author=self.viewer,
            comment="What is the answer?",
        )
        question = VideoQuestion.objects.create(comment=question_comment)
        reply = Comment.objects.create(
            video=self.video,
            author=self.replier,
            parent=question_comment,
            comment="This is the answer.",
        )
        return question_comment, question, reply

    def test_ask_question_preserves_comment_filter_sort_and_page(self):
        self.client.force_login(self.viewer)
        target = (
            reverse("video_detail", args=[self.video.pk])
            + "?comments=questions&comments_sort=newest&comments_page=2"
        )

        response = self.client.post(
            reverse("ask_video_question", args=[self.video.pk]),
            {"comment": "Can you explain this?", "next": target},
        )

        self.assertRedirects(response, target, fetch_redirect_response=False)
        comment = Comment.objects.get(comment="Can you explain this?")
        self.assertTrue(VideoQuestion.objects.filter(comment=comment).exists())

    def test_ask_question_rejects_external_return_target(self):
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("ask_video_question", args=[self.video.pk]),
            {
                "comment": "Where should this return?",
                "next": "https://evil.example/phish",
            },
        )

        self.assertRedirects(
            response,
            reverse("video_detail", args=[self.video.pk]),
            fetch_redirect_response=False,
        )

    def test_ask_question_without_next_uses_video_detail_fallback(self):
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("ask_video_question", args=[self.video.pk]),
            {"comment": "Fallback question"},
        )

        self.assertRedirects(
            response,
            reverse("video_detail", args=[self.video.pk]),
            fetch_redirect_response=False,
        )

    def test_feature_answer_preserves_video_detail_context(self):
        unused_comment, question, reply = self.create_question_with_reply()
        self.client.force_login(self.creator)
        target = (
            reverse("video_detail", args=[self.video.pk])
            + "?comments=questions&comments_sort=newest&comments_page=3"
        )

        response = self.client.post(
            reverse("feature_question_answer", args=[reply.pk]),
            {"next": target},
        )

        self.assertRedirects(response, target, fetch_redirect_response=False)
        question.refresh_from_db()
        self.assertEqual(question.featured_reply, reply)

    def test_feature_answer_preserves_full_thread_context(self):
        question_comment, question, reply = self.create_question_with_reply()
        self.client.force_login(self.creator)
        target = reverse("comment_thread", args=[question_comment.pk])

        first = self.client.post(
            reverse("feature_question_answer", args=[reply.pk]),
            {"next": target},
        )
        self.assertRedirects(first, target, fetch_redirect_response=False)
        question.refresh_from_db()
        self.assertEqual(question.featured_reply, reply)

        second = self.client.post(
            reverse("feature_question_answer", args=[reply.pk]),
            {"next": target},
        )
        self.assertRedirects(second, target, fetch_redirect_response=False)
        question.refresh_from_db()
        self.assertIsNone(question.featured_reply)

    def test_feature_answer_rejects_external_return_target(self):
        unused_comment, question, reply = self.create_question_with_reply()
        self.client.force_login(self.creator)

        response = self.client.post(
            reverse("feature_question_answer", args=[reply.pk]),
            {"next": "https://evil.example/phish"},
        )

        self.assertRedirects(
            response,
            reverse("video_detail", args=[self.video.pk]),
            fetch_redirect_response=False,
        )
        question.refresh_from_db()
        self.assertEqual(question.featured_reply, reply)

    def test_q_and_a_forms_carry_current_return_context(self):
        question_comment, unused_question, reply = self.create_question_with_reply()

        self.client.force_login(self.creator)
        detail_target = (
            reverse("video_detail", args=[self.video.pk])
            + "?comments=questions&comments_sort=newest"
        )
        detail = self.client.get(detail_target)
        self.assertContains(
            detail,
            (
                f'name="next" value="'
                f'{reverse("video_detail", args=[self.video.pk])}'
                '?comments=questions&amp;comments_sort=newest"'
            ),
            html=False,
        )
        self.assertContains(
            detail,
            reverse("feature_question_answer", args=[reply.pk]),
        )

        thread_target = reverse("comment_thread", args=[question_comment.pk])
        thread = self.client.get(thread_target)
        self.assertContains(
            thread,
            f'name="next" value="{thread_target}"',
            html=False,
        )
        self.assertContains(
            thread,
            reverse("feature_question_answer", args=[reply.pk]),
        )
