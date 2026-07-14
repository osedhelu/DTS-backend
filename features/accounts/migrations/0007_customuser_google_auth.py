from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_password_reset_token"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="auth_provider",
            field=models.CharField(
                choices=[("local", "local"), ("google", "google")],
                default="local",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="customuser",
            name="google_uid",
            field=models.CharField(
                blank=True, max_length=128, null=True, unique=True
            ),
        ),
    ]
