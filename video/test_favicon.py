from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse


class FaviconTests(TestCase):
    def test_base_template_links_brand_favicon(self):
        response = self.client.get(reverse("video_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<link rel="icon" href="/static/video/favicon.svg" type="image/svg+xml">',
            html=True,
        )

    def test_favicon_static_asset_exists(self):
        self.assertIsNotNone(finders.find("video/favicon.svg"))
