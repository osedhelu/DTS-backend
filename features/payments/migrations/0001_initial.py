from django.db import migrations, models
import django.db.models.deletion
import features.payments.infrastructure.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("stores", "0005_opening_hours_delivery_zones"),
    ]

    operations = [
        migrations.CreateModel(
            name="StorePaymentMethod",
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
                    "method_type",
                    models.CharField(
                        choices=[
                            ("qr", "qr"),
                            ("cash", "cash"),
                            ("transfer", "transfer"),
                            ("instructions", "instructions"),
                        ],
                        max_length=20,
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("instructions", models.TextField(blank=True, default="")),
                (
                    "qr_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=features.payments.infrastructure.models.payment_qr_upload_to,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "store",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payment_methods",
                        to="stores.store",
                    ),
                ),
            ],
            options={
                "verbose_name": "método de pago",
                "verbose_name_plural": "métodos de pago",
                "db_table": "payments_store_payment_method",
                "ordering": ["sort_order", "name"],
            },
        ),
    ]
