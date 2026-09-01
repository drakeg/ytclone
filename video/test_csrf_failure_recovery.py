from django.contrib.messages import get_messages
from django.test import Client, TestCase, override_settings
from django.urls import reverse


@override_settings(CSRF_FAILURE_VIEW="video.security_views.csrf_failure")
class CsrfFailureRecoveryTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def test_ajax_stale_form_returns_structured_json_403(self):
        response = self.client.post(
            "/videos/shorts/1/like/",
            {},
            HTTP_X_CSRFTOKEN="stale-token",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
            HTTP_REFERER="http://testserver/videos/shorts/#short-1",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {
                "error": "csrf_failed",
                "message": "That form expired for security reasons. Please try again.",
            },
        )
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertNotIn("Location", response.headers)

    def test_stale_login_form_redirects_to_fresh_login_and_preserves_next(self):
        response = self.client.post(
            reverse("login"),
            {"username": "viewer", "password": "password", "next": "/videos/shorts/"},
            HTTP_X_CSRFTOKEN="stale-token",
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'{reverse("login")}?next=%2Fvideos%2Fshorts%2F')
        self.assertIn(
            "That form expired for security reasons. Please try again.",
            [str(message) for message in get_messages(response.wsgi_request)],
        )

    def test_external_login_next_is_not_reflected(self):
        response = self.client.post(
            reverse("login"),
            {"next": "https://example.com/escape"},
            HTTP_X_CSRFTOKEN="stale-token",
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))

    def test_other_stale_form_returns_to_same_origin_referer(self):
        response = self.client.post(
            "/videos/shorts/1/like/",
            {},
            HTTP_X_CSRFTOKEN="stale-token",
            HTTP_REFERER="http://testserver/videos/shorts/#short-1",
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "http://testserver/videos/shorts/#short-1")

    def test_other_stale_form_rejects_external_referer(self):
        response = self.client.post(
            "/videos/shorts/1/like/",
            {},
            HTTP_X_CSRFTOKEN="stale-token",
            HTTP_REFERER="https://example.com/escape",
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("video_list"))
