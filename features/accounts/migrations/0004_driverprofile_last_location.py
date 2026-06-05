from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_devicetoken"),
    ]

    operations = [
        migrations.AddField(
            model_name="driverprofile",
            name="last_latitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="last_longitude",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
