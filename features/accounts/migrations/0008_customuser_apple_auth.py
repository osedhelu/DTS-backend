from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_customuser_google_auth"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="apple_uid",
            field=models.CharField(
                blank=True,
                max_length=128,
                null=True,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="customuser",
            name="auth_provider",
            field=models.CharField(
                choices=[
                    ("local", "local"),
                    ("google", "google"),
                    ("apple", "apple"),
                ],
                default="local",
                max_length=20,
            ),
        ),
    ]
