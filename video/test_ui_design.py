from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse


class InterfaceDesignTests(TestCase):
    def test_shared_shell_has_accessible_navigation_and_search(self):
        response = self.client.get(reverse("video_list"))

        self.assertContains(response, 'href="#main-content"')
        self.assertContains(response, 'aria-label="Primary navigation"')
        self.assertContains(response, "Search videos, channels, and playlists", count=2)
        self.assertContains(response, 'name="viewport"')

    def test_authenticated_shell_keeps_creator_destinations(self):
        user = User.objects.create_user(username="creator", password="password123")
        self.client.force_login(user)

        response = self.client.get(reverse("video_list"))

        for route_name in (
            "upload",
            "notification_list",
            "playlist_list",
            "watch_history",
            "creator_video_list",
            "creator_analytics",
            "creator_comment_list",
        ):
            with self.subTest(route_name=route_name):
                self.assertContains(response, reverse(route_name))

    def test_design_system_includes_mobile_focus_and_motion_safeguards(self):
        stylesheet_path = finders.find("style.css")
        self.assertIsNotNone(stylesheet_path)
        with open(stylesheet_path, encoding="utf-8") as stylesheet:
            css = stylesheet.read()

        self.assertIn("@media (max-width: 760px)", css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn(".skip-link:focus", css)
