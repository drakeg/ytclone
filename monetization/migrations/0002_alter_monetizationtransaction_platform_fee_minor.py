from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("monetization", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="monetizationtransaction",
            name="platform_fee_minor",
            field=models.IntegerField(default=0),
        ),
    ]
