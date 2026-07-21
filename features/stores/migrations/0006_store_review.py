from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("stores", "0005_opening_hours_delivery_zones"),
        ("accounts", "0010_customer_profile_addresses"),
        ("orders", "0002_order_service_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="StoreReview",
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
                ("rating", models.PositiveSmallIntegerField()),
                ("comment", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="store_reviews",
                        to="accounts.customuser",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviews",
                        to="orders.order",
                    ),
                ),
                (
                    "store",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reviews",
                        to="stores.store",
                    ),
                ),
            ],
            options={
                "verbose_name": "reseña",
                "verbose_name_plural": "reseñas",
                "db_table": "stores_review",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="storereview",
            constraint=models.CheckConstraint(
                condition=models.Q(("rating__gte", 1), ("rating__lte", 5)),
                name="store_review_rating_range",
            ),
        ),
    ]
