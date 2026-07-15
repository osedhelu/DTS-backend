from django.conf import settings
from django.db import models

from features.orders.infrastructure.models import Order


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
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_orderchatmessage"
        verbose_name = "mensaje de chat"
        verbose_name_plural = "mensajes de chat"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Chat order={self.order_id} from={self.sender_id}"
