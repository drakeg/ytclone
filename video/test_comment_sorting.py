from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Video
from .qa_models import VideoQuestion


class CommentSortToggleTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="sort-creator",
            password="password123",
        )
        self.viewer = User.objects.create_user(
            username="sort-viewer",
            password="password123",
        )
        self.video = Video.objects.create(
            title="Comment sorting video",
            description="Comment sort coverage",
            thumbnail="videos/comment-sort.jpg",
            video_file="videos/comment-sort.mp4",
            author=self.creator,
        )

    def create_comment(self, text, *, question=False):
        comment = Comment.objects.create(
            video=self.video,
            author=self.viewer,
            comment=text,
        )
        if question:
            VideoQuestion.objects.create(comment=comment)
        return comment

    def test_default_sort_remains_oldest_first(self):
        comments = [
            self.create_comment(f"Oldest sort {index}")
            for index in range(1, 4)
        ]

        response = self.client.get(
            reverse("video_detail", kwargs={"pk": self.video.pk})
        )
        content = response.content.decode()

        positions = [content.index(comment.comment) for comment in comments]
        self.assertEqual(positions, sorted(positions))
        self.assertContains(response, 'aria-label="Comment sort"', html=False)
        self.assertContains(response, ">Oldest</a>", html=False)

    def test_newest_sort_reverses_top_level_comment_order(self):
        comments = [
            self.create_comment(f"Newest sort {index}")
            for index in range(1, 4)
        ]

        response = self.client.get(
            reverse("video_detail", kwargs={"pk": self.video.pk}),
            {"comments_sort": "newest"},
        )
        content = response.content.decode()

        positions = [content.index(comment.comment) for comment in comments]
        self.assertEqual(positions, sorted(positions, reverse=True))

    def test_invalid_sort_falls_back_to_oldest(self):
        comments = [
            self.create_comment(f"Fallback sort {index}")
            for index in range(1, 4)
        ]

        response = self.client.get(
            reverse("video_detail", kwargs={"pk": self.video.pk}),
            {"comments_sort": "popular"},
        )
        content = response.content.decode()

        positions = [content.index(comment.comment) for comment in comments]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(response.context["selected_comment_sort"], "oldest")

    def test_questions_filter_combines_with_newest_sort_before_pagination(self):
        for index in range(1, 4):
            self.create_comment(f"Normal sort comment {index}")
        questions = [
            self.create_comment(f"Sorted question {index:02d}", question=True)
            for index in range(1, 12)
        ]

        first_page = self.client.get(
            reverse("video_detail", kwargs={"pk": self.video.pk}),
            {"comments": "questions", "comments_sort": "newest"},
        )
        content = first_page.content.decode()

        self.assertNotContains(first_page, "Normal sort comment")
        self.assertContains(first_page, questions[-1].comment)
        self.assertNotContains(first_page, questions[0].comment)
        self.assertLess(
            content.index(questions[-1].comment),
            content.index(questions[-2].comment),
        )
        self.assertContains(
            first_page,
            "comments=questions&amp;comments_sort=newest&amp;comments_page=2",
        )

        second_page = self.client.get(
            reverse("video_detail", kwargs={"pk": self.video.pk}),
            {
                "comments": "questions",
                "comments_sort": "newest",
                "comments_page": 2,
            },
        )
        self.assertContains(second_page, questions[0].comment)
        self.assertNotContains(second_page, questions[-1].comment)

    def test_sort_links_preserve_filter_and_reset_page(self):
        response = self.client.get(
            reverse("video_detail", kwargs={"pk": self.video.pk}),
            {
                "comments": "questions",
                "comments_sort": "newest",
                "comments_page": 4,
            },
        )

        detail = reverse("video_detail", kwargs={"pk": self.video.pk})
        self.assertContains(
            response,
            f'href="{detail}?comments=questions#comments-heading"',
            html=False,
        )
        self.assertContains(
            response,
            f'href="{detail}?comments=questions&amp;comments_sort=newest#comments-heading"',
            html=False,
        )
        self.assertNotContains(
            response,
            "comments_page=4#comments-heading",
            html=False,
        )

    def test_shared_video_sort_links_stay_on_shared_route(self):
        self.video.publication_status = Video.PublicationStatus.UNLISTED
        self.video.save(update_fields=["publication_status"])
        self.create_comment("Shared newest comment")

        shared_url = reverse(
            "shared_video_detail",
            kwargs={"token": self.video.share_token},
        )
        response = self.client.get(
            shared_url,
            {"comments_sort": "newest"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'href="{shared_url}?comments_sort=newest#comments-heading"',
            html=False,
        )
        self.assertNotContains(
            response,
            reverse("video_detail", kwargs={"pk": self.video.pk})
            + "?comments_sort=newest",
            html=False,
        )
