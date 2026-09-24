from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

from .models import Channel


class InterfaceDesignTests(TestCase):
    def test_shared_shell_has_accessible_navigation_and_search(self):
        response = self.client.get(reverse("video_list"))

        self.assertContains(response, 'href="#main-content"')
        self.assertContains(response, 'aria-label="Primary navigation"')
        self.assertContains(response, "Search videos, channels, and playlists", count=2)
        self.assertContains(response, 'name="viewport"')

    def test_authenticated_shell_keeps_creator_destinations(self):
        user = User.objects.create_user(username="creator", password="password123")
        Channel.objects.create(
            owner=user,
            name="Creator channel",
            description="Creator channel",
            thumbnail="channels/creator.jpg",
        )
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

        self.assertContains(response, 'method="post" action="{}"'.format(reverse("logout")))
        self.assertNotContains(response, 'href="{}"'.format(reverse("logout")))

    def test_logout_post_returns_to_working_homepage(self):
        user = User.objects.create_user(username="viewer", password="password123")
        self.client.force_login(user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("video_list"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_design_system_includes_mobile_focus_and_motion_safeguards(self):
        stylesheet_path = finders.find("style.css")
        self.assertIsNotNone(stylesheet_path)
        with open(stylesheet_path, encoding="utf-8") as stylesheet:
            css = stylesheet.read()

        self.assertIn("@media (max-width: 760px)", css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn(".skip-link:focus", css)


    def test_bulk_selection_script_has_accessible_selection_state(self):
        script_path = finders.find("video/bulk_selection.js")
        self.assertIsNotNone(script_path)
        with open(script_path, encoding="utf-8") as script_file:
            script = script_file.read()

        self.assertIn("[data-bulk-selection]", script)
        self.assertIn("data-bulk-selection-status", script)
        self.assertIn("submit.disabled = selected === 0", script)
        self.assertIn("selectAll.indeterminate", script)

    def test_bulk_selection_script_loads_only_on_bulk_list_routes(self):
        user = User.objects.create_user(username="bulk-viewer", password="password123")
        self.client.force_login(user)

        for route_name in (
            "video_bookmark_list",
            "watch_later",
            "watch_history",
            "notification_list",
        ):
            with self.subTest(route_name=route_name):
                self.assertContains(
                    self.client.get(reverse(route_name)),
                    "video/bulk_selection.js",
                )

        self.assertNotContains(
            self.client.get(reverse("video_list")),
            "video/bulk_selection.js",
        )
