import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("orders", "0002_order_service_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeliveryTracking",
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
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "order",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="delivery_tracking",
                        to="orders.order",
                    ),
                ),
            ],
            options={
                "verbose_name": "seguimiento de entrega",
                "verbose_name_plural": "seguimientos de entrega",
                "db_table": "delivery_deliverytracking",
            },
        ),
        migrations.CreateModel(
            name="TrackingPoint",
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
                    "location",
                    django.contrib.gis.db.models.fields.PointField(srid=4326),
                ),
                ("sequence", models.PositiveIntegerField()),
                ("recorded_at", models.DateTimeField()),
                (
                    "tracking",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="points",
                        to="delivery.deliverytracking",
                    ),
                ),
            ],
            options={
                "verbose_name": "punto de tracking",
                "verbose_name_plural": "puntos de tracking",
                "db_table": "delivery_trackingpoint",
                "ordering": ["sequence"],
            },
        ),
        migrations.AddConstraint(
            model_name="trackingpoint",
            constraint=models.UniqueConstraint(
                fields=("tracking", "sequence"),
                name="uniq_delivery_tracking_point_sequence",
            ),
        ),
    ]
