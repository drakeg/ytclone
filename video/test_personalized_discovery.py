from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .metadata_models import Hashtag, Tag
from .models import Category, Channel, Video, WatchHistory
from .services.discovery import DISCOVERY_SECTION_LIMIT, get_discovery_sections


class PersonalizedDiscoveryTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator-personalized", password="password123")
        self.viewer = User.objects.create_user(username="viewer-personalized", password="password123")
        self.other = User.objects.create_user(username="other-personalized", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Followed Channel", description="Follow me")
        self.category = Category.objects.create(name="Travel", description="Travel videos")

    def video(self, title, *, channel=None, category=None, audience=Video.Audience.EVERYONE):
        return Video.objects.create(
            title=title,
            description=title,
            thumbnail=f"videos/thumbnails/{title}.jpg",
            video_file=f"videos/files/{title}.mp4",
            author=self.creator,
            channel=channel,
            category=category,
            audience=audience,
        )

    def test_followed_channels_recommend_unwatched_visible_uploads(self):
        self.channel.subscribers.add(self.viewer)
        watched = self.video("watched-followed", channel=self.channel)
        unwatched = self.video("unwatched-followed", channel=self.channel)
        WatchHistory.objects.create(user=self.viewer, video=watched)

        sections = get_discovery_sections(self.viewer)

        self.assertEqual(list(sections.followed_channel_videos), [unwatched])

    def test_topic_recommendations_use_current_viewer_history(self):
        watched = self.video("watched-travel", category=self.category)
        recommended = self.video("recommended-travel", category=self.category)
        unrelated = self.video("unrelated")
        WatchHistory.objects.create(user=self.viewer, video=watched)

        sections = get_discovery_sections(self.viewer)

        self.assertIn(recommended, list(sections.recommended_videos))
        self.assertNotIn(watched, list(sections.recommended_videos))
        self.assertNotIn(unrelated, list(sections.recommended_videos))

    def test_other_users_history_does_not_personalize_viewer(self):
        watched = self.video("other-watched", category=self.category)
        candidate = self.video("other-candidate", category=self.category)
        WatchHistory.objects.create(user=self.other, video=watched)

        sections = get_discovery_sections(self.viewer)

        self.assertNotIn(candidate, list(sections.recommended_videos))
        self.assertEqual(sections.topic_signals, ())

    def test_tag_and_hashtag_signals_are_private_bounded_and_ranked(self):
        first = self.video("first")
        second = self.video("second")
        travel = Tag.objects.create(name="travel")
        camping = Tag.objects.create(name="camping")
        roadtrip = Hashtag.objects.create(name="roadtrip")
        first.tags.add(travel, camping)
        second.tags.add(travel)
        first.hashtags.add(roadtrip)
        WatchHistory.objects.create(user=self.viewer, video=first)
        WatchHistory.objects.create(user=self.viewer, video=second)

        sections = get_discovery_sections(self.viewer)

        self.assertEqual(sections.topic_signals[0].name, "travel")
        self.assertEqual(sections.topic_signals[0].count, 2)
        self.assertLessEqual(len(sections.topic_signals), 6)

    def test_personalized_recommendations_respect_visibility(self):
        watched = self.video("watched-visible", category=self.category)
        public = self.video("public-candidate", category=self.category)
        members = self.video("members-candidate", channel=self.channel, category=self.category, audience=Video.Audience.MEMBERS_ONLY)
        WatchHistory.objects.create(user=self.viewer, video=watched)

        sections = get_discovery_sections(self.viewer)

        self.assertIn(public, list(sections.recommended_videos))
        self.assertNotIn(members, list(sections.recommended_videos))

    def test_sections_remain_bounded(self):
        self.channel.subscribers.add(self.viewer)
        for number in range(DISCOVERY_SECTION_LIMIT + 2):
            self.video(f"followed-{number}", channel=self.channel)

        sections = get_discovery_sections(self.viewer)

        self.assertEqual(len(sections.followed_channel_videos), DISCOVERY_SECTION_LIMIT)

    def test_anonymous_homepage_has_no_personalized_sections(self):
        response = self.client.get(reverse("video_list"))

        self.assertNotContains(response, "From channels you follow")
        self.assertNotContains(response, "Because you watched")
        self.assertNotContains(response, "Topics you watch")

    def test_authenticated_homepage_renders_personalized_sections_when_available(self):
        self.channel.subscribers.add(self.viewer)
        followed = self.video("followed-home", channel=self.channel)
        watched = self.video("watched-home", category=self.category)
        self.video("topic-home", category=self.category)
        WatchHistory.objects.create(user=self.viewer, video=watched)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("video_list"))

        self.assertContains(response, "From channels you follow")
        self.assertContains(response, followed.title)
        self.assertContains(response, "Because you watched")
