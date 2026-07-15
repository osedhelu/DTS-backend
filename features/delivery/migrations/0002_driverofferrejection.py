import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("delivery", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("orders", "0002_order_service_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="DriverOfferRejection",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "driver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="offer_rejections",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="offer_rejections",
                        to="orders.order",
                    ),
                ),
            ],
            options={
                "verbose_name": "rechazo de oferta",
                "verbose_name_plural": "rechazos de oferta",
                "db_table": "delivery_driverofferrejection",
            },
        ),
        migrations.AddConstraint(
            model_name="driverofferrejection",
            constraint=models.UniqueConstraint(
                fields=("order", "driver"),
                name="uniq_delivery_offer_rejection_order_driver",
            ),
        ),
    ]
