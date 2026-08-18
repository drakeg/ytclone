from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("video", "0013_channelmembership"),
    ]

    operations = [
        migrations.AlterField(
            model_name="channel",
            name="thumbnail",
            field=models.ImageField(
                blank=True,
                upload_to="channels/thumbnails",
            ),
        ),
    ]
