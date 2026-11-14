import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .channel_views import CHANNEL_DIRECTORY_PAGE_SIZE
from .models import Channel, Video
from .moderation_models import ChannelModerationState


class ChannelDirectoryTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.media_directory = tempfile.TemporaryDirectory()
        cls.media_override = override_settings(MEDIA_ROOT=cls.media_directory.name)
        cls.media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.media_override.disable()
        cls.media_directory.cleanup()

    def setUp(self):
        self.owner = User.objects.create_user(username="creator", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.channel = Channel.objects.create(
            owner=self.owner,
            name="Creator Channel",
            description="A channel with useful videos and a growing community.",
        )
        self.channel.subscribers.add(self.viewer)

    def _video(self, title, *, status=Video.PublicationStatus.PUBLISHED, audience=Video.Audience.EVERYONE):
        return Video.objects.create(
            title=title,
            description="Description",
            thumbnail=SimpleUploadedFile("thumb.jpg", b"image", content_type="image/jpeg"),
            video_file=SimpleUploadedFile("video.mp4", b"video", content_type="video/mp4"),
            author=self.owner,
            channel=self.channel,
            publication_status=status,
            audience=audience,
        )

    def test_directory_renders_channel_identity_and_stats(self):
        self._video("Public video")
        self._video("Draft video", status=Video.PublicationStatus.DRAFT)
        self._video("Members video", audience=Video.Audience.MEMBERS_ONLY)

        response = self.client.get(reverse("channel_list"))

        self.assertContains(response, "Creator Channel")
        self.assertContains(response, "@creator")
        self.assertContains(response, "1 subscriber")
        self.assertContains(response, "1 public video")
        self.assertContains(response, reverse("channel_detail", args=[self.channel.pk]))
        self.assertContains(response, reverse("user_profile", args=[self.owner.username]))

    def test_channel_without_thumbnail_uses_letter_avatar_in_directory(self):
        response = self.client.get(reverse("channel_list"))
        body = response.content.decode()

        self.assertContains(response, "Creator Channel default channel avatar")
        self.assertIn("C", body)
        self.assertContains(response, "border-radius: 50%")

    def test_channel_without_thumbnail_uses_letter_avatar_on_channel_page(self):
        response = self.client.get(reverse("channel_detail", args=[self.channel.pk]))

        self.assertContains(response, "Creator Channel default channel avatar")
        self.assertContains(response, "font-weight: 850")
        self.assertContains(response, "border-radius: 50%")

    def test_uploaded_thumbnail_replaces_default_letter_avatar(self):
        self.channel.thumbnail = SimpleUploadedFile(
            "channel.jpg", b"image", content_type="image/jpeg"
        )
        self.channel.save(update_fields=["thumbnail"])

        response = self.client.get(reverse("channel_detail", args=[self.channel.pk]))

        self.assertContains(response, "channel.jpg")
        self.assertNotContains(response, "default channel avatar")

    def test_owner_sees_creator_actions_for_own_channel(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("channel_list"))

        self.assertContains(response, "Your channel")
        self.assertContains(response, reverse("monetization:creator_dashboard", args=[self.channel.pk]))

    def test_empty_directory_has_useful_empty_state(self):
        Channel.objects.all().delete()
        response = self.client.get(reverse("channel_list"))

        self.assertContains(response, "No channels yet")
        self.assertNotContains(response, "View channel")


    def _directory_channel(self, index, *, prefix="Channel"):
        owner = User.objects.create_user(
            username=f"directory-owner-{prefix.lower().replace(' ', '-')}-{index:02d}",
            password="password123",
        )
        return Channel.objects.create(
            owner=owner,
            name=f"{prefix} {index:02d}",
            description=f"{prefix} directory description {index:02d}",
        )

    def test_directory_is_paginated_at_twenty_four(self):
        for index in range(CHANNEL_DIRECTORY_PAGE_SIZE + 3):
            self._directory_channel(index)

        first = self.client.get(reverse("channel_list"))
        second = self.client.get(reverse("channel_list"), {"page": 2})

        self.assertEqual(len(first.context["channels"]), CHANNEL_DIRECTORY_PAGE_SIZE)
        self.assertEqual(first.context["channels"].paginator.num_pages, 2)
        self.assertContains(first, "Page 1 of 2")
        self.assertEqual(len(second.context["channels"]), 4)
        self.assertContains(second, "Page 2 of 2")

    def test_directory_search_matches_name_description_and_owner_username(self):
        road_owner = User.objects.create_user(
            username="roadcreator",
            password="password123",
        )
        road = Channel.objects.create(
            owner=road_owner,
            name="Road Trips",
            description="RV travel and campground adventures",
        )
        garage_owner = User.objects.create_user(
            username="garagebuilder",
            password="password123",
        )
        garage = Channel.objects.create(
            owner=garage_owner,
            name="Garage Projects",
            description="Workshop builds and repairs",
        )

        name_response = self.client.get(reverse("channel_list"), {"q": "road trips"})
        self.assertContains(name_response, road.name)
        self.assertNotContains(name_response, garage.name)

        description_response = self.client.get(
            reverse("channel_list"),
            {"q": "WORKSHOP BUILDS"},
        )
        self.assertContains(description_response, garage.name)
        self.assertNotContains(description_response, road.name)

        owner_response = self.client.get(
            reverse("channel_list"),
            {"q": "roadcreator"},
        )
        self.assertContains(owner_response, road.name)
        self.assertNotContains(owner_response, garage.name)

    def test_directory_search_filters_before_pagination_and_preserves_query(self):
        for index in range(CHANNEL_DIRECTORY_PAGE_SIZE + 1):
            self._directory_channel(index, prefix="Trail Channel")
        self._directory_channel(99, prefix="Different")

        response = self.client.get(reverse("channel_list"), {"q": "trail"})

        page = response.context["channels"]
        self.assertEqual(page.paginator.count, CHANNEL_DIRECTORY_PAGE_SIZE + 1)
        self.assertEqual(page.paginator.num_pages, 2)
        self.assertContains(response, "q=trail&amp;page=2")

    def test_directory_search_is_trimmed_and_blank_is_unfiltered(self):
        road = Channel.objects.create(
            owner=User.objects.create_user(
                username="trim-road-owner",
                password="password123",
            ),
            name="Trim Road",
            description="Search trimming",
        )

        trimmed = self.client.get(
            reverse("channel_list"),
            {"q": "  trim road  "},
        )
        self.assertEqual(trimmed.context["channel_query"], "trim road")
        self.assertContains(trimmed, road.name)

        blank = self.client.get(reverse("channel_list"), {"q": "   "})
        self.assertEqual(blank.context["channel_query"], "")
        self.assertContains(blank, self.channel.name)
        self.assertContains(blank, road.name)

    def test_directory_search_form_resets_page(self):
        response = self.client.get(
            reverse("channel_list"),
            {"q": "creator", "page": 4},
        )

        self.assertContains(response, 'name="q" value="creator"', html=False)
        self.assertNotContains(response, 'name="page"', html=False)

    def test_suspended_channels_remain_hidden_from_non_staff_search(self):
        ChannelModerationState.objects.create(channel=self.channel)

        anonymous = self.client.get(
            reverse("channel_list"),
            {"q": "creator channel"},
        )
        self.assertNotContains(anonymous, self.channel.name)

        self.client.force_login(self.owner)
        owner_response = self.client.get(
            reverse("channel_list"),
            {"q": "creator channel"},
        )
        self.assertNotContains(owner_response, self.channel.name)

    def test_staff_can_search_suspended_channels(self):
        ChannelModerationState.objects.create(channel=self.channel)
        staff = User.objects.create_user(
            username="directory-staff",
            password="password123",
            is_staff=True,
        )
        self.client.force_login(staff)

        response = self.client.get(
            reverse("channel_list"),
            {"q": "creator channel"},
        )

        self.assertContains(response, self.channel.name)

    def test_popularity_order_and_counts_survive_pagination_query(self):
        second_subscriber = User.objects.create_user(
            username="second-subscriber",
            password="password123",
        )
        self.channel.subscribers.add(second_subscriber)
        self._video("Public one")
        self._video("Public two")
        self._video(
            "Members only",
            audience=Video.Audience.MEMBERS_ONLY,
        )
        self._video(
            "Draft video two",
            status=Video.PublicationStatus.DRAFT,
        )
        lesser_owner = User.objects.create_user(
            username="lesser-owner",
            password="password123",
        )
        lesser = Channel.objects.create(
            owner=lesser_owner,
            name="Lesser Channel",
            description="Channel with fewer subscribers",
        )
        lesser.subscribers.add(self.viewer)

        response = self.client.get(reverse("channel_list"))
        channels = list(response.context["channels"].object_list)

        self.assertEqual(channels[0].pk, self.channel.pk)
        self.assertEqual(channels[0].subscriber_count, 2)
        self.assertEqual(channels[0].public_video_count, 2)
        lesser_result = next(item for item in channels if item.pk == lesser.pk)
        self.assertEqual(lesser_result.subscriber_count, 1)
        self.assertEqual(lesser_result.public_video_count, 0)
