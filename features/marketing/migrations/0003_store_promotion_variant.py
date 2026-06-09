import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketing", "0002_store_promotion"),
        ("products", "0004_category_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="storepromotionmodel",
            name="variant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="promotions",
                to="products.productvariant",
            ),
        ),
    ]
