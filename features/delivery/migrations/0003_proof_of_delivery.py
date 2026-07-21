from django.db import migrations, models
import django.db.models.deletion
import features.delivery.infrastructure.models


class Migration(migrations.Migration):
    dependencies = [
        ("delivery", "0002_driverofferrejection"),
        ("orders", "0003_order_payment_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProofOfDelivery",
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
                    "photo",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=features.delivery.infrastructure.models.proof_photo_upload_to,
                    ),
                ),
                ("signature_data", models.TextField(blank=True, default="")),
                ("notes", models.TextField(blank=True, default="")),
                ("delivered_at", models.DateTimeField(auto_now_add=True)),
                (
                    "driver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="proofs_of_delivery",
                        to="accounts.customuser",
                    ),
                ),
                (
                    "order",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="proof_of_delivery",
                        to="orders.order",
                    ),
                ),
            ],
            options={
                "verbose_name": "prueba de entrega",
                "verbose_name_plural": "pruebas de entrega",
                "db_table": "delivery_proof_of_delivery",
            },
        ),
    ]
