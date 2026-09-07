from datetime import timedelta

from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Channel, Video
from .shorts_models import VideoShort
from .services.recommendations import WATCH_RECOMMENDATION_LIMIT, watch_recommendations


class WatchRecommendationTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="recommend-creator", password="password123")
        self.viewer = User.objects.create_user(username="recommend-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Recommend Channel", description="Recommend")
        self.other_channel = Channel.objects.create(owner=self.viewer, name="Other Channel", description="Other")
        self.category = Category.objects.create(name="Travel")
        self.other_category = Category.objects.create(name="Cooking")
        self.current = self.video("Current", channel=self.channel, category=self.category)

    def video(self, title, *, channel=None, category=None, status=Video.PublicationStatus.PUBLISHED, audience=Video.Audience.EVERYONE):
        return Video.objects.create(
            title=title,
            description=title,
            thumbnail=f"videos/thumbnails/{title}.jpg",
            video_file=f"videos/files/{title}.mp4",
            author=(channel or self.channel).owner,
            channel=channel or self.channel,
            category=category,
            publication_status=status,
            audience=audience,
        )

    def test_ranks_category_then_channel_then_catalog(self):
        catalog = self.video("Catalog", channel=self.other_channel, category=self.other_category)
        same_channel = self.video("Same channel", channel=self.channel, category=self.other_category)
        same_category = self.video("Same category", channel=self.other_channel, category=self.category)

        results = list(watch_recommendations(self.current, AnonymousUser()))

        self.assertEqual(results[:3], [same_category, same_channel, catalog])
        self.assertNotIn(self.current, results)

    def test_excludes_shorts_and_hidden_videos(self):
        visible = self.video("Visible", channel=self.other_channel, category=self.category)
        short = self.video("Short", channel=self.other_channel, category=self.category)
        VideoShort.objects.create(video=short)
        draft = self.video("Draft", channel=self.other_channel, category=self.category, status=Video.PublicationStatus.DRAFT)
        members = self.video("Members", channel=self.other_channel, category=self.category, audience=Video.Audience.MEMBERS_ONLY)

        results = list(watch_recommendations(self.current, AnonymousUser()))

        self.assertEqual(results, [visible])
        self.assertNotIn(short, results)
        self.assertNotIn(draft, results)
        self.assertNotIn(members, results)

    def test_is_bounded_and_newest_first_within_rank(self):
        videos = [self.video(f"Candidate {number}", channel=self.other_channel, category=self.category) for number in range(10)]
        for number, candidate in enumerate(videos):
            Video.objects.filter(pk=candidate.pk).update(pub_date=timezone.now() - timedelta(days=number))

        results = list(watch_recommendations(self.current, AnonymousUser()))

        self.assertEqual(len(results), WATCH_RECOMMENDATION_LIMIT)
        self.assertEqual(results[0].pk, videos[0].pk)

    def test_watch_page_renders_recommendations(self):
        candidate = self.video("Watch next candidate", channel=self.other_channel, category=self.category)

        response = self.client.get(reverse("video_detail", args=[self.current.pk]))

        self.assertContains(response, "Watch next")
        self.assertContains(response, candidate.title)
        self.assertContains(response, reverse("video_detail", args=[candidate.pk]))
