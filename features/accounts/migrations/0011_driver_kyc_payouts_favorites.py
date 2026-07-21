from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0010_customer_profile_addresses"),
    ]

    operations = [
        migrations.AddField(
            model_name="driverprofile",
            name="bank_account_number",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="bank_account_type",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="bank_name",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="id_document_url",
            field=models.URLField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="verification_status",
            field=models.CharField(
                choices=[
                    ("pending", "pending"),
                    ("approved", "approved"),
                    ("rejected", "rejected"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="DriverPayoutRequest",
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
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "pending"),
                            ("paid", "paid"),
                            ("rejected", "rejected"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True, default="")),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "driver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payout_requests",
                        to="accounts.customuser",
                    ),
                ),
            ],
            options={
                "verbose_name": "solicitud de retiro",
                "verbose_name_plural": "solicitudes de retiro",
                "db_table": "accounts_driver_payout_request",
                "ordering": ["-requested_at"],
            },
        ),
        migrations.CreateModel(
            name="FavoriteStore",
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
                    "store",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="favorited_by",
                        to="stores.store",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="favorite_stores",
                        to="accounts.customuser",
                    ),
                ),
            ],
            options={
                "verbose_name": "tienda favorita",
                "verbose_name_plural": "tiendas favoritas",
                "db_table": "accounts_favorite_store",
            },
        ),
        migrations.AddConstraint(
            model_name="favoritestore",
            constraint=models.UniqueConstraint(
                fields=("user", "store"),
                name="unique_favorite_store_per_user",
            ),
        ),
    ]
