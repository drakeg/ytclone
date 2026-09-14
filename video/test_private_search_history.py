from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .search_history_models import SearchHistory
from .services.search_history import recent_searches, record_search


class PrivateSearchHistoryTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.search_url = reverse("search")

    def test_anonymous_and_blank_searches_are_not_recorded(self):
        self.client.get(self.search_url, {"query": "anonymous trail"})
        self.assertFalse(SearchHistory.objects.exists())

        self.client.force_login(self.viewer)
        self.client.get(self.search_url, {"query": "   "})
        self.assertFalse(SearchHistory.objects.exists())

    def test_authenticated_searches_are_normalized_and_case_deduplicated(self):
        self.client.force_login(self.viewer)
        self.client.get(self.search_url, {"query": "  Trail   Camera  "})
        self.client.get(self.search_url, {"query": "trail camera"})

        self.assertEqual(SearchHistory.objects.filter(user=self.viewer).count(), 1)
        self.assertEqual(SearchHistory.objects.get(user=self.viewer).query, "trail camera")

    def test_recent_searches_are_private_newest_first_and_bounded(self):
        for index in range(12):
            record_search(self.viewer, f"query {index}")
        record_search(self.other, "other private search")

        recent = list(recent_searches(self.viewer))

        self.assertEqual(len(recent), 10)
        self.assertEqual(recent[0].query, "query 11")
        self.assertEqual(recent[-1].query, "query 2")
        self.assertNotIn("other private search", [entry.query for entry in recent])

    def test_blank_search_page_shows_only_current_viewers_recent_searches(self):
        record_search(self.viewer, "Finger Lakes")
        record_search(self.other, "Private other query")
        self.client.force_login(self.viewer)

        response = self.client.get(self.search_url)

        self.assertContains(response, "Recent searches")
        self.assertContains(response, "Finger Lakes")
        self.assertContains(response, "Clear history")
        self.assertNotContains(response, "Private other query")
        self.assertContains(response, "?query=Finger%20Lakes")

    def test_clear_history_is_post_only_in_effect_and_scoped_to_current_viewer(self):
        record_search(self.viewer, "mine")
        record_search(self.other, "theirs")
        self.client.force_login(self.viewer)

        response = self.client.post(self.search_url, {"action": "clear_history"})

        self.assertRedirects(response, self.search_url)
        self.assertFalse(SearchHistory.objects.filter(user=self.viewer).exists())
        self.assertTrue(SearchHistory.objects.filter(user=self.other).exists())

    def test_anonymous_clear_is_forbidden_and_unrecognized_posts_are_rejected(self):
        self.assertEqual(
            self.client.post(self.search_url, {"action": "clear_history"}).status_code,
            403,
        )
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.post(self.search_url, {"action": "other"}).status_code, 405)
