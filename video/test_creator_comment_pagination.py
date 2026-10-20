from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Video


class CreatorCommentPaginationTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="moderation-page-creator",
            password="password123",
        )
        self.commenter = User.objects.create_user(
            username="moderation-page-commenter",
            password="password123",
        )
        self.video = Video.objects.create(
            title="Moderation pagination video",
            description="Moderation pagination coverage",
            thumbnail="videos/moderation-pagination.jpg",
            video_file="videos/moderation-pagination.mp4",
            author=self.creator,
        )
        self.client.force_login(self.creator)

    def create_comment(self, text, *, hidden=False):
        return Comment.objects.create(
            video=self.video,
            author=self.commenter,
            comment=text,
            is_hidden=hidden,
        )

    def test_moderation_queue_is_paginated_at_twenty_five(self):
        comments = [
            self.create_comment(f"Moderation comment {index:02d}")
            for index in range(1, 28)
        ]

        first_page = self.client.get(reverse("creator_comment_list"))

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(len(first_page.context["comments"]), 25)
        self.assertContains(first_page, "Page 1 of 2")
        for comment in comments[-25:]:
            self.assertContains(first_page, comment.comment)
        for comment in comments[:2]:
            self.assertNotContains(first_page, comment.comment)

        second_page = self.client.get(
            reverse("creator_comment_list"),
            {"page": 2},
        )
        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(len(second_page.context["comments"]), 2)
        for comment in comments[:2]:
            self.assertContains(second_page, comment.comment)

    def test_filter_is_applied_before_pagination(self):
        for index in range(1, 27):
            self.create_comment(f"Visible moderation {index:02d}")
        hidden = [
            self.create_comment(f"Hidden moderation {index:02d}", hidden=True)
            for index in range(1, 27)
        ]

        response = self.client.get(
            reverse("creator_comment_list"),
            {"status": "hidden"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["comments"]), 25)
        self.assertContains(response, "Page 1 of 2")
        self.assertNotContains(response, "Visible moderation")
        self.assertContains(response, hidden[-1].comment)
        self.assertContains(
            response,
            "status=hidden&amp;page=2",
        )

    def test_status_filter_links_reset_pagination(self):
        response = self.client.get(
            reverse("creator_comment_list"),
            {"status": "hidden", "page": 3},
        )

        base = reverse("creator_comment_list")
        self.assertContains(
            response,
            f'href="{base}?status=all"',
            html=False,
        )
        self.assertContains(
            response,
            f'href="{base}?status=visible"',
            html=False,
        )
        self.assertContains(
            response,
            f'href="{base}?status=hidden"',
            html=False,
        )
        self.assertNotContains(response, "status=hidden&amp;page=3", html=False)

    def test_bulk_action_preserves_current_filter_and_page(self):
        target = reverse("creator_comment_list") + "?status=visible&page=2"
        comment = self.create_comment("Preserve moderation return")

        response = self.client.post(
            reverse("creator_comment_bulk_moderation"),
            {
                "comment_ids": [comment.pk],
                "action": "hide",
                "next": target,
            },
        )

        self.assertRedirects(response, target, fetch_redirect_response=False)
        comment.refresh_from_db()
        self.assertTrue(comment.is_hidden)

    def test_bulk_action_rejects_external_return_target(self):
        comment = self.create_comment("Reject external moderation return")

        response = self.client.post(
            reverse("creator_comment_bulk_moderation"),
            {
                "comment_ids": [comment.pk],
                "action": "hide",
                "next": "https://evil.example/phish",
            },
        )

        self.assertRedirects(
            response,
            reverse("creator_comment_list"),
            fetch_redirect_response=False,
        )

    def test_invalid_page_values_fall_back_safely(self):
        for index in range(1, 28):
            self.create_comment(f"Fallback moderation {index:02d}")

        invalid = self.client.get(
            reverse("creator_comment_list"),
            {"page": "not-a-number"},
        )
        self.assertEqual(invalid.status_code, 200)
        self.assertEqual(invalid.context["comments"].number, 1)

        out_of_range = self.client.get(
            reverse("creator_comment_list"),
            {"page": 999},
        )
        self.assertEqual(out_of_range.status_code, 200)
        self.assertEqual(
            out_of_range.context["comments"].number,
            out_of_range.context["comments"].paginator.num_pages,
        )
