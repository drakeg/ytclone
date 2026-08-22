from django.apps import AppConfig


class VideoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "video"

    def ready(self):
        # Community models live in a focused module but belong to the video app.
        from . import community_models  # noqa: F401
