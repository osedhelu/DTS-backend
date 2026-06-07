# Generated manually for T6.1.2

from django.db import migrations, models
import django.db.models.deletion
import uuid


def mark_existing_users_verified(apps, schema_editor):
    CustomUser = apps.get_model("accounts", "CustomUser")
    CustomUser.objects.all().update(email_verified=True)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_driverprofile_last_location"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(mark_existing_users_verified, migrations.RunPython.noop),
        migrations.CreateModel(
            name="EmailVerificationToken",
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
                ("token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("expires_at", models.DateTimeField()),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="verification_tokens",
                        to="accounts.customuser",
                    ),
                ),
            ],
            options={
                "verbose_name": "token de verificación email",
                "verbose_name_plural": "tokens de verificación email",
                "db_table": "accounts_email_verification_token",
            },
        ),
    ]
