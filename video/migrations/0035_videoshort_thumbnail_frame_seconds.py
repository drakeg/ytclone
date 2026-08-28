from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("video", "0034_videoshort_text_overlay")]

    operations = [
        migrations.AddField(
            model_name="videoshort",
            name="thumbnail_frame_seconds",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
