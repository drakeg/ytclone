import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("video", "0011_comment_is_hidden")]

    operations = [
        migrations.AddField(
            model_name="comment",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="replies",
                to="video.comment",
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="kind",
            field=models.CharField(
                choices=[
                    ("comment", "Comment"),
                    ("reply", "Reply"),
                    ("like", "Like"),
                    ("dislike", "Dislike"),
                    ("subscription", "Subscription"),
                    ("upload", "New upload"),
                ],
                max_length=20,
            ),
        ),
    ]
