# Generated manually for configurable work/search radii

from django.db import migrations, models


def copy_driver_gps_to_work_center(apps, schema_editor):
    DriverProfile = apps.get_model("accounts", "DriverProfile")
    for profile in DriverProfile.objects.filter(
        last_latitude__isnull=False,
        last_longitude__isnull=False,
        work_center_latitude__isnull=True,
    ):
        profile.work_center_latitude = profile.last_latitude
        profile.work_center_longitude = profile.last_longitude
        profile.save(
            update_fields=["work_center_latitude", "work_center_longitude"]
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0011_driver_kyc_payouts_favorites"),
    ]

    operations = [
        migrations.AddField(
            model_name="driverprofile",
            name="work_center_latitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="work_center_longitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="work_radius_km",
            field=models.FloatField(default=5.0),
        ),
        migrations.AddField(
            model_name="customerprofile",
            name="search_center_latitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="customerprofile",
            name="search_center_longitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="customerprofile",
            name="search_radius_km",
            field=models.FloatField(default=5.0),
        ),
        migrations.RunPython(copy_driver_gps_to_work_center, migrations.RunPython.noop),
    ]
