from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("video", "0015_optional_video_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="video",
            name="audience",
            field=models.CharField(
                choices=[
                    ("everyone", "Everyone"),
                    ("members", "Paid members only"),
                ],
                default="everyone",
                max_length=12,
            ),
        ),
    ]
