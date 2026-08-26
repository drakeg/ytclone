from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("video", "0026_videoquestion"),
    ]

    operations = [
        migrations.AddField(
            model_name="video",
            name="public_release_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
