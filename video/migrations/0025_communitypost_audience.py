from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("video", "0024_video_tags_hashtags"),
    ]

    operations = [
        migrations.AddField(
            model_name="communitypost",
            name="audience",
            field=models.CharField(
                choices=[("everyone", "Everyone"), ("members", "Paid members only")],
                default="everyone",
                max_length=12,
            ),
        ),
    ]
