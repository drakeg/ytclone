from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("video", "0035_videoshort_thumbnail_frame_seconds")]

    operations = [
        migrations.AddField(
            model_name="video",
            name="captions_file",
            field=models.FileField(blank=True, upload_to="videos/captions"),
        ),
    ]
