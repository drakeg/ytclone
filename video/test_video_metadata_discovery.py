from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.urls import reverse

from .forms import VideoEditForm
from .metadata_models import Hashtag
from .models import Channel, Video
from .services.search import search_content


class VideoMetadataDiscoveryTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="metadata_creator", password="password123")
        self.viewer = User.objects.create_user(username="metadata_viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Metadata Channel", description="Metadata")
        self.video = Video.objects.create(
            title="RV Trip #UpstateNY",
            description="Camping near the falls #Travel #upstateny",
            thumbnail="videos/thumbnails/metadata.jpg",
            video_file="videos/files/metadata.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )

    def _edit_form(self, **overrides):
        data = {
            "title": self.video.title,
            "description": self.video.description,
            "category": "",
            "channel": str(self.channel.pk),
            "publication_status": Video.PublicationStatus.PUBLISHED,
            "audience": Video.Audience.EVERYONE,
            "publish_at": "",
            "tags": "RV Travel, camping, rv travel",
            "chapters": "",
        }
        data.update(overrides)
        return VideoEditForm(data, instance=self.video, user=self.creator)

    def test_hashtags_are_derived_and_deduplicated_case_insensitively(self):
        names = list(self.video.hashtags.values_list("name", flat=True))
        self.assertEqual(names, ["travel", "upstateny"])

    def test_structured_tags_are_optional_normalized_and_saved(self):
        form = self._edit_form()
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(
            list(self.video.tags.order_by("name").values_list("name", flat=True)),
            ["camping", "rv travel"],
        )

    def test_editing_title_and_description_replaces_indexed_hashtags(self):
        form = self._edit_form(
            title="Updated #RoadTrip",
            description="No old tags here",
            tags="",
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(
            list(self.video.hashtags.values_list("name", flat=True)),
            ["roadtrip"],
        )
        self.assertFalse(Hashtag.objects.get(name="upstateny").videos.filter(pk=self.video.pk).exists())

    def test_search_matches_structured_tags(self):
        form = self._edit_form(tags="camping, fifth wheel")
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        results = search_content("fifth wheel", "relevance", AnonymousUser())
        self.assertEqual(list(results.videos), [self.video])

    def test_search_accepts_hash_prefixed_hashtag(self):
        results = search_content("#UpstateNY", "relevance", AnonymousUser())
        self.assertEqual(list(results.videos), [self.video])

    def test_hashtag_page_uses_central_visibility_rules(self):
        hidden = Video.objects.create(
            title="Secret #UpstateNY",
            description="Hidden",
            thumbnail="videos/thumbnails/hidden.jpg",
            video_file="videos/files/hidden.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        response = self.client.get(reverse("hashtag_detail", args=["upstateny"]))
        self.assertContains(response, self.video.title)
        self.assertNotContains(response, hidden.title)

    def test_video_cards_link_indexed_hashtags(self):
        response = self.client.get(reverse("hashtag_detail", args=["upstateny"]))
        self.assertContains(response, reverse("hashtag_detail", args=["upstateny"]))
        self.assertContains(response, "#upstateny")

    def test_too_many_tags_is_rejected(self):
        tags = ",".join(f"tag-{number}" for number in range(21))
        form = self._edit_form(tags=tags)
        self.assertFalse(form.is_valid())
        self.assertIn("tags", form.errors)
