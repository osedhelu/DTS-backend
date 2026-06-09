# Generated manually for CategoryImage

import features.products.infrastructure.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0003_category_field_config_product_dynamic_values"),
    ]

    operations = [
        migrations.CreateModel(
            name="CategoryImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        upload_to=features.products.infrastructure.models.category_image_upload_to
                    ),
                ),
                ("is_primary", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="images",
                        to="products.category",
                    ),
                ),
            ],
            options={
                "db_table": "products_category_image",
                "ordering": ["-is_primary", "id"],
            },
        ),
    ]
