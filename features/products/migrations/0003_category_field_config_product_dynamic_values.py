from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0002_product_catalog_enrichment"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="field_config",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="product",
            name="dynamic_values",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
