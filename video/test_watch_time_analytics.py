import json
import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Video, VideoWatchEvent
from .services.analytics import get_creator_analytics


class WatchTimeAnalyticsTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.video = Video.objects.create(title="Measured", description="Watch", thumbnail="videos/t.jpg", video_file="videos/files/v.mp4", author=self.creator)

    def payload(self, **changes):
        payload = {"event_id": str(uuid.uuid4()), "playback_session_id": str(uuid.uuid4()), "watched_seconds": 10, "position_seconds": 30, "duration_seconds": 100}
        payload.update(changes)
        return payload

    def post(self, payload, video=None):
        return self.client.post(reverse("watch_time_event", args=[(video or self.video).pk]), data=json.dumps(payload), content_type="application/json")

    def test_anonymous_heartbeat_is_recorded_without_raw_session_identifier(self):
        response = self.post(self.payload())
        self.assertEqual(response.status_code, 200)
        event = VideoWatchEvent.objects.get()
        self.assertIsNone(event.viewer)
        self.assertEqual(len(event.viewer_session_hash), 64)
        self.assertNotEqual(event.viewer_session_hash, self.client.session.session_key)

    def test_event_id_is_idempotent(self):
        payload = self.payload()
        self.assertTrue(self.post(payload).json()["created"])
        self.assertFalse(self.post(payload).json()["created"])
        self.assertEqual(VideoWatchEvent.objects.count(), 1)

    def test_invalid_and_inaccessible_events_are_rejected(self):
        for changes in ({"watched_seconds": 16}, {"watched_seconds": 0}, {"duration_seconds": 0}, {"position_seconds": 101}, {"event_id": "bad"}):
            with self.subTest(changes=changes):
                self.assertEqual(self.post(self.payload(**changes)).status_code, 400)
        self.video.publication_status = Video.PublicationStatus.DRAFT
        self.video.save(update_fields=["publication_status"])
        self.assertEqual(self.post(self.payload()).status_code, 404)

    def test_authenticated_event_keeps_viewer_private_from_creator_output(self):
        self.client.force_login(self.other)
        self.post(self.payload())
        self.client.force_login(self.creator)
        response = self.client.get(reverse("creator_analytics"))
        self.assertNotContains(response, self.other.username)

    def test_metrics_aggregate_sessions_and_retention(self):
        first_session, second_session = uuid.uuid4(), uuid.uuid4()
        for session, watched, position in ((first_session, 10, 30), (first_session, 10, 60), (second_session, 10, 100)):
            self.post(self.payload(playback_session_id=str(session), watched_seconds=watched, position_seconds=position))
        video = list(get_creator_analytics(self.creator).videos)[0]
        self.assertEqual(video.watch_seconds, 30)
        self.assertEqual(video.playback_count, 2)
        self.assertEqual(video.average_view_seconds, 15)
        self.assertEqual(video.average_percentage, 15)
        self.assertEqual(video.retention, {"25": 100, "50": 100, "75": 50, "100": 50})

    def test_metrics_are_owner_scoped_and_support_28_day_range(self):
        old = self.payload()
        recent = self.payload()
        self.post(old)
        self.post(recent)
        VideoWatchEvent.objects.filter(event_id=old["event_id"]).update(created_at=timezone.now() - timedelta(days=29))
        analytics = get_creator_analytics(self.creator, days=28)
        self.assertEqual(analytics.total_watch_seconds, 10)
        self.assertNotIn("viewer_session_hash", self.client.get(reverse("creator_analytics")).content.decode())
