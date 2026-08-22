from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .models import Video


class MigrationConfigurationTests(TestCase):
    def test_video_app_is_migrated_through_latest_schema(self):
        loader = MigrationLoader(connection)
        self.assertIn("video", loader.migrated_apps)
        self.assertIn(
            ("video", "0022_video_chapters"),
            loader.graph.leaf_nodes("video"),
        )

    def test_migrated_video_table_is_available(self):
        self.assertEqual(Video.objects.count(), 0)


class RootRouteTests(SimpleTestCase):
    def test_root_redirects_to_working_application(self):
        response = self.client.get("/")
        self.assertRedirects(response, reverse("video_list"), fetch_redirect_response=False)
