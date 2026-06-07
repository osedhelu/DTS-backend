import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketing", "0001_initial"),
        ("products", "0001_initial"),
        ("stores", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="StorePromotionModel",
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
                ("name", models.CharField(max_length=255)),
                ("discount_type", models.CharField(max_length=10)),
                ("discount_value", models.DecimalField(decimal_places=2, max_digits=12)),
                ("valid_from", models.DateTimeField(blank=True, null=True)),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="promotions",
                        to="products.product",
                    ),
                ),
                (
                    "store",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="promotions",
                        to="stores.store",
                    ),
                ),
            ],
            options={
                "verbose_name": "promoción de tienda",
                "verbose_name_plural": "promociones de tienda",
                "db_table": "marketing_store_promotion",
                "ordering": ["-created_at"],
            },
        ),
    ]
