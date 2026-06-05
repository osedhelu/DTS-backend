import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0002_customerprofile_driverprofile_merchantprofile"),
    ]

    operations = [
        migrations.CreateModel(
            name="Store",
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
                (
                    "status",
                    models.CharField(default="closed", max_length=10),
                ),
                (
                    "location",
                    django.contrib.gis.db.models.fields.PointField(srid=4326),
                ),
                ("address", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="stores",
                        to="accounts.customuser",
                    ),
                ),
            ],
            options={
                "verbose_name": "comercio",
                "verbose_name_plural": "comercios",
                "db_table": "stores_store",
            },
        ),
    ]
