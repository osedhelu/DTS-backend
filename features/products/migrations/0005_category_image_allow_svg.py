from django.db import migrations, models

import features.products.infrastructure.models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0004_category_image"),
    ]

    operations = [
        migrations.AlterField(
            model_name="categoryimage",
            name="image",
            field=models.FileField(
                upload_to=features.products.infrastructure.models.category_image_upload_to,
            ),
        ),
    ]
