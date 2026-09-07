from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("video", "0036_video_captions_file"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubscriptionNotificationPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("upload_notifications_enabled", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("channel", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notification_preferences", to="video.channel")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="subscription_notification_preferences", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "constraints": [models.UniqueConstraint(fields=("user", "channel"), name="unique_subscription_notification_preference")],
            },
        ),
    ]
