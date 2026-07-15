from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_customuser_apple_auth"),
    ]

    operations = [
        migrations.AddField(
            model_name="driverprofile",
            name="full_name",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="vehicle_plate",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="photo_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="onboarding_completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
