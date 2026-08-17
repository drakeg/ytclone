import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("video", "0012_comment_parent_notification_reply"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChannelMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("editor", "Editor")], default="editor", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("channel", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="video.channel")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="channel_memberships", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="channelmembership",
            constraint=models.UniqueConstraint(fields=("channel", "user"), name="unique_channel_team_member"),
        ),
    ]
