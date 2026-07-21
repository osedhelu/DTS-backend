from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0009_driverprofile_onboarding"),
    ]

    operations = [
        migrations.AddField(
            model_name="customerprofile",
            name="full_name",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="customerprofile",
            name="photo_url",
            field=models.URLField(blank=True),
        ),
        migrations.CreateModel(
            name="CustomerAddress",
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
                ("label", models.CharField(max_length=100)),
                ("address", models.TextField()),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
                ("is_default", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="customer_addresses",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "dirección cliente",
                "verbose_name_plural": "direcciones cliente",
                "db_table": "accounts_customer_address",
                "ordering": ["-is_default", "-updated_at"],
            },
        ),
    ]
