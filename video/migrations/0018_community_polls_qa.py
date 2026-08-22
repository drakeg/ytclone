from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("video", "0017_communitypost_communityreply"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="communitypost",
            name="kind",
            field=models.CharField(
                choices=[("update", "Update"), ("question", "Question"), ("poll", "Poll")],
                default="update",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="communitypost",
            name="featured_reply",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="featured_on_posts",
                to="video.communityreply",
            ),
        ),
        migrations.CreateModel(
            name="CommunityPollOption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.CharField(max_length=240)),
                ("position", models.PositiveSmallIntegerField(default=0)),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="poll_options", to="video.communitypost")),
            ],
            options={"ordering": ["position", "pk"]},
        ),
        migrations.CreateModel(
            name="CommunityPollVote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("option", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="votes", to="video.communitypolloption")),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="poll_votes", to="video.communitypost")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="community_poll_votes", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="communitypollvote",
            constraint=models.UniqueConstraint(fields=("post", "user"), name="unique_user_per_community_poll"),
        ),
    ]
