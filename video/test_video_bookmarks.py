from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .bookmark_views import SAVED_MOMENTS_PAGE_SIZE
from .models import Video, VideoBookmark
from .services.bookmarks import BookmarkValidationError, save_bookmark


class VideoBookmarkTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.video = Video.objects.create(
            title="Bookmark video",
            description="Video",
            thumbnail="videos/t.jpg",
            video_file="videos/v.mp4",
            author=self.owner,
        )

    def test_bookmark_routes_require_login_and_mutations_require_post(self):
        list_url = reverse("video_bookmark_list")
        create_url = reverse("video_bookmark_create", args=[self.video.pk])
        self.assertRedirects(self.client.get(list_url), f"/accounts/login/?next={list_url}")
        self.assertRedirects(self.client.post(create_url), f"/accounts/login/?next={create_url}")
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(create_url).status_code, 405)

    def test_viewer_can_save_and_relabel_the_same_moment(self):
        self.client.force_login(self.viewer)
        url = reverse("video_bookmark_create", args=[self.video.pk])
        self.assertRedirects(
            self.client.post(url, {"position_seconds": "62.4", "label": " First idea "}),
            reverse("video_detail", args=[self.video.pk]),
        )
        bookmark = VideoBookmark.objects.get()
        self.assertEqual((bookmark.position_seconds, bookmark.label), (62, "First idea"))
        self.client.post(url, {"position_seconds": "62", "label": "Updated idea"})
        self.assertEqual(VideoBookmark.objects.count(), 1)
        self.assertEqual(VideoBookmark.objects.get().label, "Updated idea")

    def test_service_rejects_invalid_labels_and_positions(self):
        invalid_values = [
            ("", 10),
            ("x" * 121, 10),
            ("Label", -1),
            ("Label", 86401),
            ("Label", "nan"),
            ("Label", "not-a-number"),
        ]
        for label, position in invalid_values:
            with self.subTest(label=label[:10], position=position), self.assertRaises(BookmarkValidationError):
                save_bookmark(user=self.viewer, video=self.video, position=position, label=label)
        self.assertFalse(VideoBookmark.objects.exists())

    def test_viewer_cannot_bookmark_an_inaccessible_video(self):
        self.video.publication_status = Video.PublicationStatus.DRAFT
        self.video.save(update_fields=["publication_status"])
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("video_bookmark_create", args=[self.video.pk]),
            {"position_seconds": 5, "label": "Forged"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(VideoBookmark.objects.exists())

    def test_video_page_lists_only_current_viewers_bookmarks_in_time_order(self):
        VideoBookmark.objects.create(user=self.viewer, video=self.video, position_seconds=90, label="Later")
        VideoBookmark.objects.create(user=self.viewer, video=self.video, position_seconds=5, label="Sooner")
        VideoBookmark.objects.create(user=self.other, video=self.video, position_seconds=1, label="Private note")
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("video_detail", args=[self.video.pk]))
        self.assertContains(response, 'data-seek-time="5"')
        self.assertContains(response, "0:05 · Sooner")
        self.assertNotContains(response, "Private note")
        self.assertLess(response.content.index("0:05 · Sooner".encode()), response.content.index("1:30 · Later".encode()))
        self.assertContains(response, 'id="bookmark-position"')
        self.assertContains(response, "player.currentTime")

    def test_private_list_contains_only_owned_accessible_bookmarks(self):
        own = VideoBookmark.objects.create(user=self.viewer, video=self.video, position_seconds=5, label="Mine")
        VideoBookmark.objects.create(user=self.other, video=self.video, position_seconds=10, label="Not mine")
        hidden = Video.objects.create(
            title="Hidden",
            description="Draft",
            thumbnail="videos/h.jpg",
            video_file="videos/h.mp4",
            author=self.owner,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        VideoBookmark.objects.create(user=self.viewer, video=hidden, position_seconds=2, label="No longer visible")
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("video_bookmark_list"))
        self.assertContains(response, own.label)
        self.assertNotContains(response, "Not mine")
        self.assertNotContains(response, "No longer visible")

    def test_saved_moments_are_paginated_newest_first(self):
        for index in range(SAVED_MOMENTS_PAGE_SIZE + 3):
            VideoBookmark.objects.create(
                user=self.viewer,
                video=self.video,
                position_seconds=index,
                label=f"Moment {index:02d}",
            )

        self.client.force_login(self.viewer)
        first_page = self.client.get(reverse("video_bookmark_list"))
        bookmarks = first_page.context["bookmarks"]
        self.assertEqual(bookmarks.number, 1)
        self.assertEqual(bookmarks.paginator.num_pages, 2)
        self.assertEqual(len(bookmarks.object_list), SAVED_MOMENTS_PAGE_SIZE)
        self.assertContains(first_page, "Moment 26")
        self.assertNotContains(first_page, "Moment 02")
        self.assertContains(first_page, "Page 1 of 2")
        self.assertContains(first_page, "?page=2")

        second_page = self.client.get(reverse("video_bookmark_list"), {"page": 2})
        bookmarks = second_page.context["bookmarks"]
        self.assertEqual(bookmarks.number, 2)
        self.assertEqual(len(bookmarks.object_list), 3)
        self.assertContains(second_page, "Moment 02")
        self.assertContains(second_page, "Moment 00")
        self.assertNotContains(second_page, "Moment 26")

    def test_saved_moments_invalid_pages_fall_back_safely(self):
        for index in range(SAVED_MOMENTS_PAGE_SIZE + 1):
            VideoBookmark.objects.create(
                user=self.viewer,
                video=self.video,
                position_seconds=index,
                label=f"Moment {index:02d}",
            )

        self.client.force_login(self.viewer)
        invalid = self.client.get(reverse("video_bookmark_list"), {"page": "not-a-page"})
        self.assertEqual(invalid.context["bookmarks"].number, 1)
        out_of_range = self.client.get(reverse("video_bookmark_list"), {"page": 999})
        self.assertEqual(out_of_range.context["bookmarks"].number, 2)

    def test_list_removal_preserves_current_page(self):
        bookmark = VideoBookmark.objects.create(
            user=self.viewer,
            video=self.video,
            position_seconds=5,
            label="Mine",
        )
        self.client.force_login(self.viewer)
        url = reverse("video_bookmark_delete", args=[bookmark.pk])
        expected = f'{reverse("video_bookmark_list")}?page=2'
        self.assertRedirects(
            self.client.post(url, {"source": "list", "page": "2"}),
            expected,
            fetch_redirect_response=False,
        )
        self.assertFalse(VideoBookmark.objects.filter(pk=bookmark.pk).exists())

    def test_removal_is_post_only_and_owner_scoped(self):
        bookmark = VideoBookmark.objects.create(user=self.viewer, video=self.video, position_seconds=5, label="Mine")
        url = reverse("video_bookmark_delete", args=[bookmark.pk])
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(VideoBookmark.objects.filter(pk=bookmark.pk).exists())
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), reverse("video_detail", args=[self.video.pk]))
        self.assertFalse(VideoBookmark.objects.exists())

    def test_bookmarks_cascade_when_video_is_permanently_deleted(self):
        VideoBookmark.objects.create(user=self.viewer, video=self.video, position_seconds=5, label="Mine")
        self.video.delete()
        self.assertFalse(VideoBookmark.objects.exists())

    def test_saved_moments_search_matches_label_and_video_title(self):
        other_video = Video.objects.create(
            title="Garden walkthrough",
            description="Video",
            thumbnail="videos/g.jpg",
            video_file="videos/g.mp4",
            author=self.owner,
        )
        label_match = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=10, label="Important setup note"
        )
        title_match = VideoBookmark.objects.create(
            user=self.viewer, video=other_video, position_seconds=20, label="Watch this"
        )
        VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=30, label="Unrelated"
        )
        self.client.force_login(self.viewer)

        label_response = self.client.get(reverse("video_bookmark_list"), {"q": "SETUP"})
        self.assertEqual(list(label_response.context["bookmarks"].object_list), [label_match])

        title_response = self.client.get(reverse("video_bookmark_list"), {"q": "garden"})
        self.assertEqual(list(title_response.context["bookmarks"].object_list), [title_match])

    def test_saved_moments_search_filters_before_pagination_and_preserves_query(self):
        for index in range(SAVED_MOMENTS_PAGE_SIZE + 1):
            VideoBookmark.objects.create(
                user=self.viewer,
                video=self.video,
                position_seconds=index,
                label=f"Needle moment {index:02d}",
            )
        VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=100, label="Different"
        )
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("video_bookmark_list"), {"q": "Needle"})
        bookmarks = response.context["bookmarks"]
        self.assertEqual(bookmarks.paginator.count, SAVED_MOMENTS_PAGE_SIZE + 1)
        self.assertEqual(bookmarks.paginator.num_pages, 2)
        self.assertEqual(response.context["bookmark_query"], "Needle")
        self.assertContains(response, "q=Needle&amp;page=2")

    def test_saved_moments_search_keeps_visibility_boundary(self):
        hidden = Video.objects.create(
            title="Secret needle video",
            description="Draft",
            thumbnail="videos/secret.jpg",
            video_file="videos/secret.mp4",
            author=self.owner,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        VideoBookmark.objects.create(
            user=self.viewer, video=hidden, position_seconds=5, label="Needle secret"
        )
        visible = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=6, label="Needle visible"
        )
        VideoBookmark.objects.create(
            user=self.other, video=self.video, position_seconds=7, label="Needle other user"
        )
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("video_bookmark_list"), {"q": "needle"})

        self.assertEqual(list(response.context["bookmarks"].object_list), [visible])

    def test_saved_moments_blank_query_behaves_unfiltered_and_no_match_has_empty_state(self):
        VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=5, label="Existing"
        )
        self.client.force_login(self.viewer)

        blank = self.client.get(reverse("video_bookmark_list"), {"q": "   "})
        self.assertEqual(blank.context["bookmark_query"], "")
        self.assertEqual(blank.context["bookmarks"].paginator.count, 1)

        missing = self.client.get(reverse("video_bookmark_list"), {"q": "nothing-here"})
        self.assertContains(missing, "No saved moments match")

    def test_list_removal_preserves_search_query_and_page(self):
        bookmark = VideoBookmark.objects.create(
            user=self.viewer,
            video=self.video,
            position_seconds=5,
            label="Needle",
        )
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("video_bookmark_delete", args=[bookmark.pk]),
            {"source": "list", "page": "2", "q": "needle & setup"},
        )

        self.assertRedirects(
            response,
            reverse("video_bookmark_list") + "?q=needle+%26+setup&page=2",
            fetch_redirect_response=False,
        )
        self.assertFalse(VideoBookmark.objects.filter(pk=bookmark.pk).exists())

    def test_saved_moments_support_bounded_sort_options(self):
        alpha_video = Video.objects.create(
            title="Alpha video",
            description="Video",
            thumbnail="videos/a.jpg",
            video_file="videos/a.mp4",
            author=self.owner,
        )
        high_timestamp = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=90, label="High"
        )
        low_timestamp = VideoBookmark.objects.create(
            user=self.viewer, video=alpha_video, position_seconds=5, label="Low"
        )
        self.client.force_login(self.viewer)

        title_response = self.client.get(
            reverse("video_bookmark_list"), {"sort": "title"}
        )
        self.assertEqual(
            list(title_response.context["bookmarks"].object_list),
            [low_timestamp, high_timestamp],
        )
        self.assertEqual(title_response.context["bookmark_sort"], "title")

        timestamp_response = self.client.get(
            reverse("video_bookmark_list"), {"sort": "timestamp"}
        )
        self.assertEqual(
            list(timestamp_response.context["bookmarks"].object_list),
            [low_timestamp, high_timestamp],
        )

    def test_invalid_saved_moments_sort_falls_back_to_newest(self):
        older = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=5, label="Older"
        )
        newer = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=6, label="Newer"
        )
        self.client.force_login(self.viewer)

        response = self.client.get(
            reverse("video_bookmark_list"), {"sort": "not-a-sort"}
        )

        self.assertEqual(response.context["bookmark_sort"], "newest")
        self.assertEqual(
            list(response.context["bookmarks"].object_list),
            [newer, older],
        )

    def test_saved_moments_sort_composes_with_search_and_pagination(self):
        for index in range(SAVED_MOMENTS_PAGE_SIZE + 1):
            VideoBookmark.objects.create(
                user=self.viewer,
                video=self.video,
                position_seconds=index,
                label=f"Needle {index:02d}",
            )
        VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=100, label="Different"
        )
        self.client.force_login(self.viewer)

        response = self.client.get(
            reverse("video_bookmark_list"),
            {"q": "needle", "sort": "timestamp"},
        )

        page = response.context["bookmarks"]
        self.assertEqual(page.paginator.count, SAVED_MOMENTS_PAGE_SIZE + 1)
        self.assertEqual(page.object_list[0].position_seconds, 0)
        self.assertContains(response, "q=needle&amp;sort=timestamp&amp;page=2")

    def test_list_removal_preserves_search_sort_and_page(self):
        bookmark = VideoBookmark.objects.create(
            user=self.viewer,
            video=self.video,
            position_seconds=5,
            label="Needle",
        )
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("video_bookmark_delete", args=[bookmark.pk]),
            {
                "source": "list",
                "page": "2",
                "q": "needle & setup",
                "sort": "timestamp",
            },
        )

        self.assertRedirects(
            response,
            reverse("video_bookmark_list")
            + "?q=needle+%26+setup&sort=timestamp&page=2",
            fetch_redirect_response=False,
        )
        self.assertFalse(VideoBookmark.objects.filter(pk=bookmark.pk).exists())

    def test_saved_moments_oldest_sort_orders_oldest_first(self):
        older = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=5, label="Older"
        )
        newer = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=6, label="Newer"
        )
        self.client.force_login(self.viewer)

        response = self.client.get(
            reverse("video_bookmark_list"), {"sort": "oldest"}
        )

        self.assertEqual(response.context["bookmark_sort"], "oldest")
        self.assertEqual(
            list(response.context["bookmarks"].object_list),
            [older, newer],
        )

    def test_saved_moments_remove_form_preserves_active_sort(self):
        bookmark = VideoBookmark.objects.create(
            user=self.viewer,
            video=self.video,
            position_seconds=5,
            label="Needle",
        )
        self.client.force_login(self.viewer)

        response = self.client.get(
            reverse("video_bookmark_list"),
            {"q": "needle", "sort": "oldest"},
        )

        self.assertContains(response, 'name="q" value="needle"')
        self.assertContains(response, 'name="sort" value="oldest"')
        self.assertContains(response, f'action="{reverse("video_bookmark_delete", args=[bookmark.pk])}"')



    def test_bulk_delete_removes_selected_visible_owned_bookmarks(self):
        first = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=5, label="First"
        )
        second = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=10, label="Second"
        )
        keep = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=15, label="Keep"
        )
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("video_bookmark_bulk_delete"),
            {"bookmark_ids": [str(first.pk), str(second.pk)]},
        )

        self.assertRedirects(response, reverse("video_bookmark_list"))
        self.assertFalse(VideoBookmark.objects.filter(pk__in=[first.pk, second.pk]).exists())
        self.assertTrue(VideoBookmark.objects.filter(pk=keep.pk).exists())

    def test_bulk_delete_is_post_only_and_owner_visibility_scoped(self):
        visible = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=5, label="Visible"
        )
        other = VideoBookmark.objects.create(
            user=self.other, video=self.video, position_seconds=6, label="Other"
        )
        hidden_video = Video.objects.create(
            title="Hidden bulk",
            description="Draft",
            thumbnail="videos/hidden-bulk.jpg",
            video_file="videos/hidden-bulk.mp4",
            author=self.owner,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        hidden = VideoBookmark.objects.create(
            user=self.viewer, video=hidden_video, position_seconds=7, label="Hidden"
        )
        self.client.force_login(self.viewer)
        url = reverse("video_bookmark_bulk_delete")

        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(
            url,
            {"bookmark_ids": [str(visible.pk), str(other.pk), str(hidden.pk)]},
        )

        self.assertFalse(VideoBookmark.objects.filter(pk=visible.pk).exists())
        self.assertTrue(VideoBookmark.objects.filter(pk=other.pk).exists())
        self.assertTrue(VideoBookmark.objects.filter(pk=hidden.pk).exists())

    def test_bulk_delete_safely_ignores_empty_malformed_and_duplicate_ids(self):
        bookmark = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=5, label="Mine"
        )
        keep = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=6, label="Keep"
        )
        self.client.force_login(self.viewer)
        url = reverse("video_bookmark_bulk_delete")

        empty = self.client.post(url, {})
        self.assertRedirects(empty, reverse("video_bookmark_list"))
        self.assertTrue(VideoBookmark.objects.filter(pk=bookmark.pk).exists())

        response = self.client.post(
            url,
            {"bookmark_ids": [str(bookmark.pk), str(bookmark.pk), "bad-id", ""]},
        )
        self.assertRedirects(response, reverse("video_bookmark_list"))
        self.assertFalse(VideoBookmark.objects.filter(pk=bookmark.pk).exists())
        self.assertTrue(VideoBookmark.objects.filter(pk=keep.pk).exists())

    def test_bulk_delete_preserves_search_sort_and_page_state(self):
        bookmark = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=5, label="Needle"
        )
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("video_bookmark_bulk_delete"),
            {
                "bookmark_ids": [str(bookmark.pk)],
                "page": "2",
                "q": "needle & setup",
                "sort": "timestamp",
            },
        )

        self.assertRedirects(
            response,
            reverse("video_bookmark_list")
            + "?q=needle+%26+setup&sort=timestamp&page=2",
            fetch_redirect_response=False,
        )

    def test_saved_moments_list_renders_bulk_selection_controls(self):
        bookmark = VideoBookmark.objects.create(
            user=self.viewer, video=self.video, position_seconds=5, label="Needle"
        )
        self.client.force_login(self.viewer)

        response = self.client.get(
            reverse("video_bookmark_list"),
            {"q": "needle", "sort": "oldest"},
        )

        self.assertContains(response, reverse("video_bookmark_bulk_delete"))
        self.assertContains(response, f'name="bookmark_ids" value="{bookmark.pk}"')
        self.assertContains(response, 'name="q" value="needle"')
        self.assertContains(response, 'name="sort" value="oldest"')
        self.assertContains(response, "Remove selected")
