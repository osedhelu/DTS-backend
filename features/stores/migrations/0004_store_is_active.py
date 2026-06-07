from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stores", "0003_store_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="store",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
