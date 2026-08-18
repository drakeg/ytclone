from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("video", "0014_alter_channel_thumbnail"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="category",
            name="thumbnail",
            field=models.ImageField(blank=True, upload_to="categories/thumbnails"),
        ),
        migrations.AlterField(
            model_name="video",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="video.category",
            ),
        ),
    ]
