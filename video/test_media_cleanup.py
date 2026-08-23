from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from .models import Category, Channel, Video
from .services.media_cleanup import cleanup_orphaned_media


class FakeStorage:
    def __init__(self, files=None, *, unknown_age=None, fail_delete=None):
        self.files = dict(files or {})
        self.unknown_age = set(unknown_age or ())
        self.fail_delete = set(fail_delete or ())
        self.deleted = []

    def listdir(self, path):
        prefix = path.strip("/") + "/"
        directories = set()
        files = set()
        for name in self.files:
            if not name.startswith(prefix):
                continue
            remainder = name[len(prefix) :]
            if not remainder:
                continue
            if "/" in remainder:
                directories.add(remainder.split("/", 1)[0])
            else:
                files.add(remainder)
        return sorted(directories), sorted(files)

    def get_modified_time(self, name):
        if name in self.unknown_age:
            raise NotImplementedError
        return self.files[name]

    def delete(self, name):
        if name in self.fail_delete:
            raise OSError("simulated delete failure")
        self.deleted.append(name)
        self.files.pop(name, None)


class MediaCleanupTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.old = self.now - timedelta(days=3)
        self.recent = self.now - timedelta(hours=2)
        owner = User.objects.create_user(username="mediaowner", password="password123")
        category = Category.objects.create(
            name="Cleanup",
            thumbnail="categories/thumbnails/category.jpg",
        )
        channel = Channel.objects.create(
            name="Cleanup Channel",
            description="Cleanup",
            thumbnail="channels/thumbnails/channel.jpg",
            owner=owner,
        )
        self.video = Video.objects.create(
            title="Trashed but referenced",
            description="Keep its files",
            thumbnail="videos/thumbnails/video.jpg",
            video_file="videos/files/video.mp4",
            author=owner,
            channel=channel,
            category=category,
            deleted_at=self.now - timedelta(days=40),
        )

    def storage(self, **kwargs):
        files = {
            "categories/thumbnails/category.jpg": self.old,
            "channels/thumbnails/channel.jpg": self.old,
            "videos/thumbnails/video.jpg": self.old,
            "videos/files/video.mp4": self.old,
            "videos/files/nested/old-orphan.mp4": self.old,
            "videos/thumbnails/recent-orphan.jpg": self.recent,
            "videos/files/unknown-age.mp4": self.old,
            "unmanaged/leave-me.bin": self.old,
        }
        return FakeStorage(files, unknown_age={"videos/files/unknown-age.mp4"}, **kwargs)

    def test_dry_run_reports_old_orphan_without_deleting_anything(self):
        storage = self.storage()
        report = cleanup_orphaned_media(
            storage, delete=False, min_age_hours=24, now=self.now
        )

        self.assertEqual(report.orphaned, ["videos/files/nested/old-orphan.mp4"])
        self.assertIn("videos/files/video.mp4", report.referenced)
        self.assertIn("videos/thumbnails/video.jpg", report.referenced)
        self.assertIn("channels/thumbnails/channel.jpg", report.referenced)
        self.assertIn("categories/thumbnails/category.jpg", report.referenced)
        self.assertEqual(report.protected_recent, ["videos/thumbnails/recent-orphan.jpg"])
        self.assertEqual(report.protected_unknown_age, ["videos/files/unknown-age.mp4"])
        self.assertEqual(storage.deleted, [])
        self.assertIn("unmanaged/leave-me.bin", storage.files)

    def test_delete_removes_only_old_known_age_orphan(self):
        storage = self.storage()
        report = cleanup_orphaned_media(
            storage, delete=True, min_age_hours=24, now=self.now
        )

        self.assertEqual(report.deleted, ["videos/files/nested/old-orphan.mp4"])
        self.assertNotIn("videos/files/nested/old-orphan.mp4", storage.files)
        self.assertIn("videos/thumbnails/recent-orphan.jpg", storage.files)
        self.assertIn("videos/files/unknown-age.mp4", storage.files)
        self.assertIn("videos/files/video.mp4", storage.files)
        self.assertIn("unmanaged/leave-me.bin", storage.files)

    def test_delete_failure_is_reported_and_object_remains(self):
        orphan = "videos/files/nested/old-orphan.mp4"
        storage = self.storage(fail_delete={orphan})
        report = cleanup_orphaned_media(
            storage, delete=True, min_age_hours=24, now=self.now
        )

        self.assertEqual(report.deleted, [])
        self.assertEqual(report.failed, [(orphan, "simulated delete failure")])
        self.assertIn(orphan, storage.files)

    def test_negative_minimum_age_is_rejected(self):
        with self.assertRaises(ValueError):
            cleanup_orphaned_media(self.storage(), min_age_hours=-1, now=self.now)

    def test_management_command_is_dry_run_by_default(self):
        storage = self.storage()
        stdout = StringIO()
        with patch(
            "video.management.commands.cleanup_orphaned_media.default_storage", storage
        ):
            call_command("cleanup_orphaned_media", stdout=stdout)

        output = stdout.getvalue()
        self.assertIn("Media cleanup mode: DRY RUN", output)
        self.assertIn("videos/files/nested/old-orphan.mp4 [would delete]", output)
        self.assertIn("Dry run complete; no media objects were deleted.", output)
        self.assertEqual(storage.deleted, [])

    def test_management_command_requires_nonnegative_minimum_age(self):
        with self.assertRaises(CommandError):
            call_command("cleanup_orphaned_media", min_age_hours=-1)
