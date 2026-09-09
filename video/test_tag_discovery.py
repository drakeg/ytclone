from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .metadata_models import Tag
from .models import Channel, Video


class TagDiscoveryTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="pw")
        self.viewer = User.objects.create_user(username="viewer", password="pw")
        self.channel = Channel.objects.create(name="Channel", description="", owner=self.creator)
        self.tag = Tag.objects.create(name="rv travel")

    def video(self, title, status=Video.PublicationStatus.PUBLISHED):
        video = Video.objects.create(
            title=title,
            description=title,
            thumbnail="videos/thumb.jpg",
            video_file="videos/video.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=status,
        )
        video.tags.add(self.tag)
        return video

    def test_tag_page_lists_only_visible_videos(self):
        visible = self.video("Visible")
        hidden = self.video("Hidden", status=Video.PublicationStatus.DRAFT)

        response = self.client.get(reverse("tag_detail", kwargs={"name": self.tag.name}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, visible.title)
        self.assertNotContains(response, hidden.title)

    def test_creator_can_see_own_draft_on_tag_page(self):
        hidden = self.video("Creator draft", status=Video.PublicationStatus.DRAFT)
        self.client.force_login(self.creator)

        response = self.client.get(reverse("tag_detail", kwargs={"name": self.tag.name}))

        self.assertContains(response, hidden.title)

    def test_unknown_tag_returns_404(self):
        response = self.client.get(reverse("tag_detail", kwargs={"name": "missing"}))
        self.assertEqual(response.status_code, 404)

    def test_watch_page_links_structured_tag(self):
        video = self.video("Tagged video")

        response = self.client.get(reverse("video_detail", kwargs={"pk": video.pk}))

        self.assertContains(response, reverse("tag_detail", kwargs={"name": self.tag.name}))
        self.assertContains(response, self.tag.name)

    def test_tag_and_hashtag_routes_are_distinct(self):
        self.assertNotEqual(
            reverse("tag_detail", kwargs={"name": "travel"}),
            reverse("hashtag_detail", kwargs={"name": "travel"}),
        )
