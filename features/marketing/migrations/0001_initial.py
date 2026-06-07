from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BannerModel",
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
                ("title", models.CharField(max_length=255)),
                ("image_url", models.URLField(max_length=500)),
                ("link_url", models.URLField(blank=True, default="", max_length=500)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "banner",
                "verbose_name_plural": "banners",
                "db_table": "marketing_banner",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.CreateModel(
            name="CouponModel",
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
                ("code", models.CharField(max_length=64, unique=True)),
                (
                    "discount_type",
                    models.CharField(
                        choices=[("PERCENTAGE", "PERCENTAGE"), ("FIXED", "FIXED")],
                        max_length=10,
                    ),
                ),
                (
                    "discount_value",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                (
                    "min_order_total",
                    models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                ("max_uses", models.PositiveIntegerField(blank=True, null=True)),
                ("used_count", models.PositiveIntegerField(default=0)),
                ("valid_from", models.DateTimeField(blank=True, null=True)),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "cupón",
                "verbose_name_plural": "cupones",
                "db_table": "marketing_coupon",
                "ordering": ["-created_at"],
            },
        ),
    ]
