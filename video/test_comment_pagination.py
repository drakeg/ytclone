from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Video
from .qa_models import VideoQuestion


class TopLevelCommentPaginationTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="pagination-creator",
            password="password123",
        )
        self.viewer = User.objects.create_user(
            username="pagination-viewer",
            password="password123",
        )
        self.video = Video.objects.create(
            title="Comment pagination video",
            description="Pagination coverage",
            thumbnail="videos/comment-pagination.jpg",
            video_file="videos/comment-pagination.mp4",
            author=self.creator,
        )

    def create_comment(self, text, *, hidden=False, question=False):
        comment = Comment.objects.create(
            video=self.video,
            author=self.viewer,
            comment=text,
            is_hidden=hidden,
        )
        if question:
            VideoQuestion.objects.create(comment=comment)
        return comment

    def test_video_detail_limits_visible_top_level_comments_to_ten(self):
        comments = [
            self.create_comment(f"Visible comment {index:02d}")
            for index in range(1, 13)
        ]

        first_page = self.client.get(
            reverse("video_detail", kwargs={"pk": self.video.pk})
        )

        self.assertEqual(first_page.status_code, 200)
        for comment in comments[:10]:
            self.assertContains(first_page, comment.comment)
        for comment in comments[10:]:
            self.assertNotContains(first_page, comment.comment)
        self.assertContains(first_page, "Page 1 of 2")
        self.assertContains(first_page, "comments_page=2")

        second_page = self.client.get(
            reverse("video_detail", kwargs={"pk": self.video.pk}),
            {"comments_page": 2},
        )
        self.assertEqual(second_page.status_code, 200)
        for comment in comments[:10]:
            self.assertNotContains(second_page, comment.comment)
        for comment in comments[10:]:
            self.assertContains(second_page, comment.comment)
        self.assertContains(second_page, "Page 2 of 2")

    def test_hidden_top_level_comments_do_not_affect_page_count(self):
        visible = [
            self.create_comment(f"Visible only {index:02d}")
            for index in range(1, 11)
        ]
        for index in range(1, 6):
            self.create_comment(f"Hidden comment {index:02d}", hidden=True)

        response = self.client.get(
            reverse("video_detail", kwargs={"pk": self.video.pk})
        )

        self.assertEqual(response.status_code, 200)
        for comment in visible:
            self.assertContains(response, comment.comment)
        self.assertNotContains(response, "Page 1 of")
        self.assertNotContains(response, "Hidden comment")

    def test_questions_filter_is_applied_before_pagination(self):
        for index in range(1, 13):
            self.create_comment(f"Normal comment {index:02d}")
        questions = [
            self.create_comment(f"Question comment {index:02d}", question=True)
            for index in range(1, 12)
        ]

        first_page = self.client.get(
            reverse("video_detail", kwargs={"pk": self.video.pk}),
            {"comments": "questions"},
        )

        self.assertEqual(first_page.status_code, 200)
        self.assertNotContains(first_page, "Normal comment")
        for question in questions[:10]:
            self.assertContains(first_page, question.comment)
        self.assertNotContains(first_page, questions[10].comment)
        self.assertContains(first_page, "Page 1 of 2")
        self.assertContains(first_page, "comments=questions&amp;comments_page=2")

        second_page = self.client.get(
            reverse("video_detail", kwargs={"pk": self.video.pk}),
            {"comments": "questions", "comments_page": 2},
        )
        self.assertEqual(second_page.status_code, 200)
        self.assertContains(second_page, questions[10].comment)
        self.assertNotContains(second_page, questions[0].comment)

    def test_invalid_and_out_of_range_pages_fall_back_safely(self):
        comments = [
            self.create_comment(f"Fallback comment {index:02d}")
            for index in range(1, 13)
        ]
        detail = reverse("video_detail", kwargs={"pk": self.video.pk})

        invalid = self.client.get(detail, {"comments_page": "not-a-number"})
        self.assertEqual(invalid.status_code, 200)
        self.assertContains(invalid, comments[0].comment)
        self.assertNotContains(invalid, comments[-1].comment)

        out_of_range = self.client.get(detail, {"comments_page": 999})
        self.assertEqual(out_of_range.status_code, 200)
        self.assertNotContains(out_of_range, comments[0].comment)
        self.assertContains(out_of_range, comments[-1].comment)

    def test_shared_video_pager_stays_on_shared_route(self):
        self.video.publication_status = Video.PublicationStatus.UNLISTED
        self.video.save(update_fields=["publication_status"])
        for index in range(1, 12):
            self.create_comment(f"Shared comment {index:02d}")

        shared_url = reverse(
            "shared_video_detail",
            kwargs={"token": self.video.share_token},
        )
        response = self.client.get(shared_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Page 1 of 2")
        self.assertContains(
            response,
            f'href="{shared_url}?comments_page=2#comments-heading"',
            html=False,
        )
        self.assertNotContains(
            response,
            f'href="{reverse("video_detail", kwargs={"pk": self.video.pk})}?comments_page=2',
            html=False,
        )
