import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("stores", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DailySalesReport",
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
                ("report_date", models.DateField()),
                ("order_count", models.PositiveIntegerField()),
                (
                    "gross_revenue",
                    models.DecimalField(decimal_places=2, max_digits=14),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "store",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="daily_sales_reports",
                        to="stores.store",
                    ),
                ),
            ],
            options={
                "verbose_name": "reporte diario de ventas",
                "verbose_name_plural": "reportes diarios de ventas",
                "db_table": "analytics_daily_sales_report",
                "ordering": ["report_date", "store_id"],
            },
        ),
        migrations.CreateModel(
            name="DriverCommission",
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
                ("report_date", models.DateField()),
                ("delivery_count", models.PositiveIntegerField()),
                (
                    "commission_amount",
                    models.DecimalField(decimal_places=2, max_digits=14),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "driver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="driver_commissions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "comisión diaria de conductor",
                "verbose_name_plural": "comisiones diarias de conductor",
                "db_table": "analytics_driver_commission",
                "ordering": ["report_date", "driver_id"],
            },
        ),
        migrations.AddConstraint(
            model_name="dailysalesreport",
            constraint=models.UniqueConstraint(
                fields=("report_date", "store"),
                name="uniq_analytics_daily_sales_report_store_date",
            ),
        ),
        migrations.AddConstraint(
            model_name="drivercommission",
            constraint=models.UniqueConstraint(
                fields=("report_date", "driver"),
                name="uniq_analytics_driver_commission_driver_date",
            ),
        ),
    ]
