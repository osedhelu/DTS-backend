# Generated manually for chat image + message_type

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderchatmessage",
            name="message_type",
            field=models.CharField(
                choices=[
                    ("text", "Texto"),
                    ("image", "Imagen"),
                    ("system", "Sistema"),
                ],
                default="text",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="orderchatmessage",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="chat/%Y/%m/",
            ),
        ),
        migrations.AlterField(
            model_name="orderchatmessage",
            name="body",
            field=models.TextField(blank=True, default="", max_length=2000),
        ),
    ]
