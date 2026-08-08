import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("video", "0005_watchhistory_playback_progress"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("comment", "Comment"), ("like", "Like"), ("dislike", "Dislike"), ("subscription", "Subscription")], max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("actor", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sent_notifications", to=settings.AUTH_USER_MODEL)),
                ("channel", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="video.channel")),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
                ("video", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="video.video")),
            ],
            options={"ordering": ["-created_at", "-pk"]},
        ),
    ]
