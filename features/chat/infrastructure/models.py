from django.conf import settings
from django.db import models

from features.orders.infrastructure.models import Order


class ChatMessageType(models.TextChoices):
    TEXT = "text", "Texto"
    IMAGE = "image", "Imagen"
    SYSTEM = "system", "Sistema"


def chat_image_upload_to(instance: "OrderChatMessage", filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    return f"chat/order_{instance.order_id}/{instance.pk or 'new'}.{extension}"


class OrderChatMessage(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    body = models.TextField(max_length=2000, blank=True, default="")
    message_type = models.CharField(
        max_length=16,
        choices=ChatMessageType.choices,
        default=ChatMessageType.TEXT,
    )
    image = models.ImageField(
        upload_to=chat_image_upload_to,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_orderchatmessage"
        verbose_name = "mensaje de chat"
        verbose_name_plural = "mensajes de chat"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Chat order={self.order_id} from={self.sender_id}"
