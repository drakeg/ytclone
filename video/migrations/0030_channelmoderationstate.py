from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("video", "0029_moderation_states_audit")]

    operations = [
        migrations.CreateModel(
            name="ChannelModerationState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("suspended_at", models.DateTimeField(auto_now_add=True)),
                ("channel", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="moderation_state", to="video.channel")),
            ],
        ),
    ]
