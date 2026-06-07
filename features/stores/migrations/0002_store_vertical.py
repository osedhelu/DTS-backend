# Generated manually for T6.1.3

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stores", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="store",
            name="vertical",
            field=models.CharField(default="FOOD", max_length=10),
        ),
    ]
