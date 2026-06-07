from django.db import migrations, models

import features.stores.infrastructure.models


class Migration(migrations.Migration):

    dependencies = [
        ("stores", "0002_store_vertical"),
    ]

    operations = [
        migrations.AddField(
            model_name="store",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="store",
            name="phone",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
        migrations.AddField(
            model_name="store",
            name="logo",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=features.stores.infrastructure.models.store_logo_upload_to,
            ),
        ),
    ]
