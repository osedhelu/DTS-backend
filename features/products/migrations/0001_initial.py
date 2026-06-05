import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("stores", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subcategories",
                        to="products.category",
                    ),
                ),
                (
                    "store",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="categories",
                        to="stores.store",
                    ),
                ),
            ],
            options={
                "verbose_name": "categoría",
                "verbose_name_plural": "categorías",
                "db_table": "products_category",
            },
        ),
        migrations.CreateModel(
            name="Product",
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
                ("description", models.TextField(blank=True)),
                ("price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("stock", models.PositiveIntegerField(default=0)),
                (
                    "product_type",
                    models.CharField(default="physical", max_length=10),
                ),
                ("requires_on_site_visit", models.BooleanField(default=False)),
                (
                    "duration_minutes",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="products",
                        to="products.category",
                    ),
                ),
                (
                    "store",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="products",
                        to="stores.store",
                    ),
                ),
                (
                    "subcategory",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="products_as_subcategory",
                        to="products.category",
                    ),
                ),
            ],
            options={
                "verbose_name": "producto",
                "verbose_name_plural": "productos",
                "db_table": "products_product",
            },
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                fields=("store", "name", "parent"),
                name="unique_category_name_per_parent",
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["store", "product_type"],
                name="products_store_type_idx",
            ),
        ),
    ]
