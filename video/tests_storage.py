from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.test import SimpleTestCase


class MediaStorageConfigurationTests(SimpleTestCase):
    def test_local_media_storage_is_the_default(self):
        self.assertFalse(settings.USE_S3_MEDIA)
        self.assertEqual(
            settings.STORAGES["default"]["BACKEND"],
            "django.core.files.storage.FileSystemStorage",
        )

    def test_default_storage_uses_local_filesystem(self):
        self.assertIsInstance(default_storage, FileSystemStorage)
