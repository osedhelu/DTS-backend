from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketing", "0003_store_promotion_variant"),
    ]

    operations = [
        migrations.AddField(
            model_name="storepromotionmodel",
            name="param_key",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="storepromotionmodel",
            name="param_value",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
