from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="customer_notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="order",
            name="duration_minutes",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="order_type",
            field=models.CharField(default="delivery", max_length=10),
        ),
        migrations.AddField(
            model_name="order",
            name="scheduled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="service_address",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="order",
            name="service_latitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="service_longitude",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
