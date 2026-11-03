from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Comment, Video


class CreatorCommentSearchTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="search-creator",
            password="password123",
        )
        self.commenter = User.objects.create_user(
            username="HelpfulViewer",
            password="password123",
        )
        self.other_creator = User.objects.create_user(
            username="foreign-search-creator",
            password="password123",
        )
        self.video = self.create_video(
            "Alabama RV Walkthrough",
            self.creator,
        )
        self.other_video = self.create_video(
            "Solar Battery Install",
            self.creator,
        )
        self.foreign_video = self.create_video(
            "Foreign Creator Video",
            self.other_creator,
        )
        self.trashed_video = self.create_video(
            "Trashed Search Video",
            self.creator,
        )
        self.trashed_video.deleted_at = timezone.now()
        self.trashed_video.save(update_fields=["deleted_at"])

        self.text_match = self.create_comment(
            self.video,
            "The STORAGE compartment is huge.",
        )
        self.author_match = self.create_comment(
            self.video,
            "Nice tour.",
        )
        self.video_match = self.create_comment(
            self.other_video,
            "Thanks for showing this.",
            hidden=True,
        )
        self.foreign = self.create_comment(
            self.foreign_video,
            "storage should never leak",
        )
        self.trashed = self.create_comment(
            self.trashed_video,
            "storage on a trashed video",
        )
        self.client.force_login(self.creator)

    def create_video(self, title, author):
        return Video.objects.create(
            title=title,
            description=title,
            thumbnail=f"videos/{title}.jpg",
            video_file=f"videos/{title}.mp4",
            author=author,
        )

    def create_comment(self, video, text, *, hidden=False):
        return Comment.objects.create(
            video=video,
            author=self.commenter,
            comment=text,
            is_hidden=hidden,
        )

    def test_search_matches_comment_text_case_insensitively(self):
        response = self.client.get(
            reverse("creator_comment_list"),
            {"query": "storage"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.text_match.comment)
        self.assertNotContains(response, self.video_match.comment)
        self.assertNotContains(response, self.foreign.comment)
        self.assertNotContains(response, self.trashed.comment)

    def test_search_matches_author_username_case_insensitively(self):
        response = self.client.get(
            reverse("creator_comment_list"),
            {"query": "helpfulviewer"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.text_match.comment)
        self.assertContains(response, self.author_match.comment)
        self.assertContains(response, self.video_match.comment)
        self.assertNotContains(response, self.foreign.comment)
        self.assertNotContains(response, self.trashed.comment)

    def test_search_matches_video_title_case_insensitively(self):
        response = self.client.get(
            reverse("creator_comment_list"),
            {"query": "solar battery"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.video_match.comment)
        self.assertNotContains(response, self.text_match.comment)

    def test_search_combines_with_status_before_pagination(self):
        for index in range(30):
            self.create_comment(
                self.video,
                f"Needle visible {index:02d}",
            )
        for index in range(30):
            self.create_comment(
                self.video,
                f"Needle hidden {index:02d}",
                hidden=True,
            )

        response = self.client.get(
            reverse("creator_comment_list"),
            {"status": "hidden", "query": "needle"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["comments"]), 25)
        self.assertEqual(response.context["comments"].paginator.count, 30)
        self.assertContains(response, "Page 1 of 2")
        self.assertNotContains(response, "Needle visible")
        self.assertContains(
            response,
            "status=hidden&amp;query=needle&amp;page=2",
        )

    def test_search_input_is_trimmed_and_blank_search_is_unfiltered(self):
        trimmed = self.client.get(
            reverse("creator_comment_list"),
            {"query": "  storage  "},
        )
        self.assertEqual(trimmed.context["selected_query"], "storage")
        self.assertContains(trimmed, self.text_match.comment)

        blank = self.client.get(
            reverse("creator_comment_list"),
            {"query": "   "},
        )
        self.assertEqual(blank.context["selected_query"], "")
        self.assertContains(blank, self.text_match.comment)
        self.assertContains(blank, self.video_match.comment)

    def test_status_links_preserve_search_and_reset_page(self):
        response = self.client.get(
            reverse("creator_comment_list"),
            {"status": "hidden", "query": "battery", "page": 4},
        )

        base = reverse("creator_comment_list")
        self.assertContains(
            response,
            f'href="{base}?status=all&amp;query=battery"',
            html=False,
        )
        self.assertContains(
            response,
            f'href="{base}?status=visible&amp;query=battery"',
            html=False,
        )
        self.assertContains(
            response,
            f'href="{base}?status=hidden&amp;query=battery"',
            html=False,
        )

    def test_search_form_preserves_status_and_resets_page(self):
        response = self.client.get(
            reverse("creator_comment_list"),
            {"status": "hidden", "query": "battery", "page": 4},
        )

        self.assertContains(
            response,
            'name="status" value="hidden"',
            html=False,
        )
        self.assertContains(
            response,
            'name="query" value="battery"',
            html=False,
        )
        self.assertNotContains(
            response,
            'name="page"',
            html=False,
        )

    def test_bulk_action_can_return_to_search_filter_and_page(self):
        target = (
            reverse("creator_comment_list")
            + "?status=visible&query=storage&page=2"
        )

        response = self.client.post(
            reverse("creator_comment_bulk_moderation"),
            {
                "comment_ids": [self.text_match.pk],
                "action": "hide",
                "next": target,
            },
        )

        self.assertRedirects(response, target, fetch_redirect_response=False)
        self.text_match.refresh_from_db()
        self.assertTrue(self.text_match.is_hidden)
