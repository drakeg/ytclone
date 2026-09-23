from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Video, WatchHistory


class WatchHistoryTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.other_viewer = User.objects.create_user(
            username="other-viewer", password="password123"
        )
        self.category = Category.objects.create(
            name="General",
            description="General videos",
            thumbnail="categories/thumbnails/general.jpg",
        )
        self.video = Video.objects.create(
            title="History test video",
            description="A test video",
            thumbnail="videos/thumbnails/history.jpg",
            video_file="videos/files/history.mp4",
            author=self.owner,
            category=self.category,
        )

    def _history_video(self, title, *, publication_status=Video.PublicationStatus.PUBLISHED):
        return Video.objects.create(
            title=title,
            description="History pagination test",
            thumbnail="videos/thumbnails/history.jpg",
            video_file=f"videos/files/{title.lower().replace(' ', '-')}.mp4",
            author=self.owner,
            category=self.category,
            publication_status=publication_status,
        )

    def test_anonymous_view_does_not_create_history(self):
        self.client.get(reverse("video_detail", kwargs={"pk": self.video.pk}))
        self.assertEqual(WatchHistory.objects.count(), 0)

    def test_authenticated_view_creates_one_history_entry(self):
        self.client.login(username="viewer", password="password123")
        url = reverse("video_detail", kwargs={"pk": self.video.pk})

        self.client.get(url)
        self.client.get(url)

        self.assertEqual(WatchHistory.objects.count(), 1)
        entry = WatchHistory.objects.get()
        self.assertEqual(entry.user, self.viewer)
        self.assertEqual(entry.video, self.video)

    def test_history_page_requires_login(self):
        response = self.client.get(reverse("watch_history"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_history_page_only_shows_current_users_entries(self):
        WatchHistory.objects.create(user=self.viewer, video=self.video)
        WatchHistory.objects.create(user=self.other_viewer, video=self.video)
        self.client.login(username="viewer", password="password123")

        response = self.client.get(reverse("watch_history"))

        self.assertContains(response, self.video.title)
        self.assertEqual(list(response.context["entries"]), [self.viewer.watch_history.get()])

    def test_history_page_paginates_visible_entries_newest_first(self):
        entries = []
        for index in range(26):
            video = self._history_video(f"History video {index:02d}")
            entries.append(WatchHistory.objects.create(user=self.viewer, video=video))
        self.client.force_login(self.viewer)

        first_page = self.client.get(reverse("watch_history"))
        second_page = self.client.get(reverse("watch_history"), {"page": 2})

        self.assertEqual(len(first_page.context["entries"]), 24)
        self.assertEqual(len(second_page.context["entries"]), 2)
        self.assertEqual(first_page.context["entries"][0].pk, entries[-1].pk)
        self.assertEqual(second_page.context["entries"][-1].pk, entries[0].pk)
        self.assertContains(first_page, "?page=2")
        self.assertContains(second_page, "?page=1")

    def test_inaccessible_entries_do_not_consume_page_slots(self):
        hidden = self._history_video(
            "Hidden history video",
            publication_status=Video.PublicationStatus.DRAFT,
        )
        WatchHistory.objects.create(user=self.viewer, video=hidden)
        for index in range(25):
            video = self._history_video(f"Visible history {index:02d}")
            WatchHistory.objects.create(user=self.viewer, video=video)
        self.client.force_login(self.viewer)

        first_page = self.client.get(reverse("watch_history"))
        second_page = self.client.get(reverse("watch_history"), {"page": 2})

        self.assertEqual(len(first_page.context["entries"]), 24)
        self.assertEqual(len(second_page.context["entries"]), 1)
        self.assertNotContains(first_page, hidden.title)
        self.assertNotContains(second_page, hidden.title)

    def test_invalid_history_page_falls_back_safely(self):
        WatchHistory.objects.create(user=self.viewer, video=self.video)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_history"), {"page": "not-a-page"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["entries"].number, 1)

    def test_user_can_remove_own_history_entry(self):
        entry = WatchHistory.objects.create(user=self.viewer, video=self.video)
        self.client.login(username="viewer", password="password123")

        response = self.client.post(
            reverse("watch_history_remove", kwargs={"pk": entry.pk})
        )

        self.assertRedirects(response, reverse("watch_history"))
        self.assertFalse(WatchHistory.objects.filter(pk=entry.pk).exists())

    def test_remove_preserves_requested_history_page(self):
        entry = WatchHistory.objects.create(user=self.viewer, video=self.video)
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("watch_history_remove", kwargs={"pk": entry.pk}),
            {"page": 2},
        )

        self.assertRedirects(response, f'{reverse("watch_history")}?page=2')
        self.assertFalse(WatchHistory.objects.filter(pk=entry.pk).exists())

    def test_user_cannot_remove_another_users_history_entry(self):
        entry = WatchHistory.objects.create(user=self.other_viewer, video=self.video)
        self.client.login(username="viewer", password="password123")

        response = self.client.post(
            reverse("watch_history_remove", kwargs={"pk": entry.pk})
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(WatchHistory.objects.filter(pk=entry.pk).exists())

    def test_clear_history_removes_only_current_users_entries(self):
        WatchHistory.objects.create(user=self.viewer, video=self.video)
        WatchHistory.objects.create(user=self.other_viewer, video=self.video)
        self.client.login(username="viewer", password="password123")

        response = self.client.post(reverse("watch_history_clear"))

        self.assertRedirects(response, reverse("watch_history"))
        self.assertFalse(WatchHistory.objects.filter(user=self.viewer).exists())
        self.assertTrue(WatchHistory.objects.filter(user=self.other_viewer).exists())

    def test_history_search_matches_video_titles_case_insensitively(self):
        match = self._history_video("Finger Lakes Adventure")
        other = self._history_video("Mountain Drive")
        WatchHistory.objects.create(user=self.viewer, video=match)
        WatchHistory.objects.create(user=self.viewer, video=other)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_history"), {"q": "finger lakes"})

        self.assertContains(response, match.title)
        self.assertNotContains(response, other.title)
        self.assertEqual(response.context["history_query"], "finger lakes")

    def test_history_search_filters_before_pagination_and_preserves_query(self):
        for index in range(25):
            video = self._history_video(f"Trail history {index:02d}")
            WatchHistory.objects.create(user=self.viewer, video=video)
        other = self._history_video("Different history")
        WatchHistory.objects.create(user=self.viewer, video=other)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_history"), {"q": "trail"})

        self.assertEqual(response.context["entries"].paginator.count, 25)
        self.assertEqual(response.context["entries"].paginator.num_pages, 2)
        self.assertContains(response, "?q=trail&page=2")

    def test_history_search_keeps_visibility_and_user_boundaries(self):
        hidden = self._history_video("Secret trail", publication_status=Video.PublicationStatus.DRAFT)
        visible = self._history_video("Visible trail")
        WatchHistory.objects.create(user=self.viewer, video=hidden)
        own = WatchHistory.objects.create(user=self.viewer, video=visible)
        WatchHistory.objects.create(user=self.other_viewer, video=visible)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_history"), {"q": "trail"})

        self.assertEqual(list(response.context["entries"].object_list), [own])
        self.assertNotContains(response, hidden.title)

    def test_history_remove_preserves_search_query_and_page(self):
        entry = WatchHistory.objects.create(user=self.viewer, video=self.video)
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("watch_history_remove", kwargs={"pk": entry.pk}),
            {"page": "2", "q": "history & test"},
        )

        self.assertRedirects(
            response,
            reverse("watch_history") + "?q=history+%26+test&page=2",
            fetch_redirect_response=False,
        )
        self.assertFalse(WatchHistory.objects.filter(pk=entry.pk).exists())

    def test_whitespace_only_history_search_is_unfiltered(self):
        WatchHistory.objects.create(user=self.viewer, video=self.video)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_history"), {"q": "   "})

        self.assertEqual(response.context["history_query"], "")
        self.assertEqual(response.context["entries"].paginator.count, 1)
        self.assertContains(response, self.video.title)

    def test_clear_history_still_clears_full_viewer_history_after_filtering(self):
        matching = self._history_video("Trail match")
        nonmatching = self._history_video("Different title")
        WatchHistory.objects.create(user=self.viewer, video=matching)
        WatchHistory.objects.create(user=self.viewer, video=nonmatching)
        self.client.force_login(self.viewer)

        response = self.client.post(reverse("watch_history_clear"))

        self.assertRedirects(response, reverse("watch_history"))
        self.assertFalse(WatchHistory.objects.filter(user=self.viewer).exists())

    def test_watch_history_supports_bounded_sort_options(self):
        alpha = self._history_video("Alpha history")
        zulu = self._history_video("Zulu history")
        alpha_entry = WatchHistory.objects.create(user=self.viewer, video=alpha)
        zulu_entry = WatchHistory.objects.create(user=self.viewer, video=zulu)
        self.client.force_login(self.viewer)

        title_response = self.client.get(
            reverse("watch_history"), {"sort": "title"}
        )

        self.assertEqual(
            list(title_response.context["entries"].object_list),
            [alpha_entry, zulu_entry],
        )
        self.assertEqual(title_response.context["history_sort"], "title")

    def test_invalid_watch_history_sort_falls_back_to_recent(self):
        older = WatchHistory.objects.create(user=self.viewer, video=self.video)
        newer_video = self._history_video("Newer history")
        newer = WatchHistory.objects.create(user=self.viewer, video=newer_video)
        self.client.force_login(self.viewer)

        response = self.client.get(
            reverse("watch_history"), {"sort": "not-a-sort"}
        )

        self.assertEqual(response.context["history_sort"], "recent")
        self.assertEqual(
            list(response.context["entries"].object_list),
            [newer, older],
        )

    def test_watch_history_sort_composes_with_search_and_pagination(self):
        for index in range(25):
            video = self._history_video(f"Trail history {index:02d}")
            WatchHistory.objects.create(user=self.viewer, video=video)
        other = self._history_video("Different history")
        WatchHistory.objects.create(user=self.viewer, video=other)
        self.client.force_login(self.viewer)

        response = self.client.get(
            reverse("watch_history"),
            {"q": "trail", "sort": "title"},
        )

        page = response.context["entries"]
        self.assertEqual(page.paginator.count, 25)
        self.assertEqual(page.object_list[0].video.title, "Trail history 00")
        self.assertContains(response, "q=trail&sort=title&page=2")

    def test_watch_history_remove_preserves_query_sort_and_page(self):
        entry = WatchHistory.objects.create(user=self.viewer, video=self.video)
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("watch_history_remove", kwargs={"pk": entry.pk}),
            {
                "page": "2",
                "q": "history & test",
                "sort": "title",
            },
        )

        self.assertRedirects(
            response,
            reverse("watch_history")
            + "?q=history+%26+test&sort=title&page=2",
            fetch_redirect_response=False,
        )
        self.assertFalse(WatchHistory.objects.filter(pk=entry.pk).exists())

