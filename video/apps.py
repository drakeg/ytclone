from django.apps import AppConfig


class VideoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "video"

    def ready(self):
        # Focused model modules belong to the video app and register signals here.
        from . import (  # noqa: F401
            community_models,
            metadata_models,
            moderation_models,
            qa_models,
            reporting_models,
            shorts_models,
        )
