from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import Channel, Video
from .shorts_models import VideoShort


class ShortsQueryScalingTests(TestCase):
    def _create_short(self, index):
        creator = User.objects.create_user(username=f"creator-{index}", password="password123")
        channel = Channel.objects.create(owner=creator, name=f"Channel {index}", description="")
        video = Video.objects.create(
            title=f"Short {index}",
            description="Query scaling test",
            thumbnail=f"videos/thumbnails/query-{index}.jpg",
            video_file=f"videos/files/query-{index}.mp4",
            author=creator,
            channel=channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=video)

    def _feed_query_count(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("shorts_feed"))
        self.assertEqual(response.status_code, 200)
        return len(queries)

    def test_channel_owner_lookup_does_not_scale_per_short(self):
        self._create_short(1)
        one_short_queries = self._feed_query_count()

        for index in range(2, 7):
            self._create_short(index)
        six_short_queries = self._feed_query_count()

        self.assertLessEqual(
            six_short_queries,
            one_short_queries + 1,
            "Shorts feed query count should remain essentially constant as channels are added.",
        )
