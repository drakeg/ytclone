import hashlib
import math
import uuid
from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from video.models import VideoWatchEvent


class InvalidWatchEvent(ValueError):
    pass


def _integer(value, minimum, maximum):
    number = float(value)
    if not math.isfinite(number):
        raise InvalidWatchEvent
    number = round(number)
    if not minimum <= number <= maximum:
        raise InvalidWatchEvent
    return number


def record_watch_event(*, video, user, session_key, payload):
    try:
        event_id = uuid.UUID(str(payload["event_id"]))
        playback_session_id = uuid.UUID(str(payload["playback_session_id"]))
        watched = _integer(payload["watched_seconds"], 1, 15)
        duration = _integer(payload["duration_seconds"], 1, 86400)
        position = _integer(payload["position_seconds"], 0, duration)
    except (KeyError, TypeError, ValueError, InvalidWatchEvent):
        raise InvalidWatchEvent("Invalid watch event.")
    session_hash = hashlib.sha256(f"{settings.SECRET_KEY}:{session_key}".encode()).hexdigest()
    try:
        with transaction.atomic():
            return VideoWatchEvent.objects.get_or_create(event_id=event_id, defaults={
                "playback_session_id": playback_session_id, "video": video,
                "viewer": user if user.is_authenticated else None,
                "viewer_session_hash": session_hash, "watched_seconds": watched,
                "position_seconds": position, "duration_seconds": duration,
            })
    except IntegrityError:
        return VideoWatchEvent.objects.get(event_id=event_id), False


def watch_metrics_for_videos(videos, days=None):
    ids = [video.pk for video in videos]
    events = VideoWatchEvent.objects.filter(video_id__in=ids)
    if days:
        events = events.filter(created_at__gte=timezone.now() - timedelta(days=days))
    sessions = defaultdict(lambda: {"watched": 0, "duration": 0, "position": 0})
    for event in events.values("video_id", "playback_session_id", "watched_seconds", "duration_seconds", "position_seconds"):
        row = sessions[(event["video_id"], event["playback_session_id"])]
        row["watched"] += event["watched_seconds"]
        row["duration"] = max(row["duration"], event["duration_seconds"])
        row["position"] = max(row["position"], event["position_seconds"])
    result = {}
    for video_id in ids:
        rows = [row for (row_video, unused), row in sessions.items() if row_video == video_id]
        total = sum(min(row["watched"], row["duration"]) for row in rows)
        count = len(rows)
        durations = sum(row["duration"] for row in rows)
        retention = {str(threshold): round(100 * sum(row["position"] * 100 >= row["duration"] * (95 if threshold == 100 else threshold) for row in rows) / count) if count else 0 for threshold in (25, 50, 75, 100)}
        result[video_id] = {"watch_seconds": total, "watch_hours": total / 3600, "playback_count": count, "average_view_seconds": round(total / count) if count else 0, "average_percentage": round(100 * total / durations) if durations else 0, "retention": retention}
    return result
