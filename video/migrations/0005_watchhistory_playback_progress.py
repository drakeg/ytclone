from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("video", "0004_watchhistory"),
    ]

    operations = [
        migrations.AddField(
            model_name="watchhistory",
            name="duration_seconds",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="watchhistory",
            name="playback_position_seconds",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
