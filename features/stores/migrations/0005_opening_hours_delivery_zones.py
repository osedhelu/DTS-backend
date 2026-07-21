from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("stores", "0004_store_is_active"),
    ]

    operations = [
        migrations.AddField(
            model_name="store",
            name="use_schedule",
            field=models.BooleanField(
                default=False,
                help_text="Si True, el estado open/closed se sincroniza con horarios.",
            ),
        ),
        migrations.CreateModel(
            name="StoreOpeningHours",
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
                ("day_of_week", models.PositiveSmallIntegerField()),
                ("open_time", models.TimeField(blank=True, null=True)),
                ("close_time", models.TimeField(blank=True, null=True)),
                ("is_closed", models.BooleanField(default=False)),
                (
                    "store",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="opening_hours",
                        to="stores.store",
                    ),
                ),
            ],
            options={
                "verbose_name": "horario de tienda",
                "verbose_name_plural": "horarios de tienda",
                "db_table": "stores_opening_hours",
                "ordering": ["day_of_week"],
            },
        ),
        migrations.CreateModel(
            name="DeliveryZone",
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
                ("name", models.CharField(default="Principal", max_length=100)),
                ("center_latitude", models.FloatField()),
                ("center_longitude", models.FloatField()),
                (
                    "radius_km",
                    models.DecimalField(decimal_places=2, default=5, max_digits=8),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "store",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="delivery_zones",
                        to="stores.store",
                    ),
                ),
            ],
            options={
                "verbose_name": "zona de entrega",
                "verbose_name_plural": "zonas de entrega",
                "db_table": "stores_delivery_zone",
            },
        ),
        migrations.AddConstraint(
            model_name="storeopeninghours",
            constraint=models.UniqueConstraint(
                fields=("store", "day_of_week"),
                name="unique_opening_hours_per_day",
            ),
        ),
    ]
