from django.db import models

from features.payments.domain.entities import PaymentMethodType
from features.stores.infrastructure.models import Store


def payment_qr_upload_to(instance: "StorePaymentMethod", filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1]
    return f"payments/store_{instance.store_id}/qr_{instance.pk or 'new'}.{extension}"


class StorePaymentMethod(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="payment_methods",
    )
    method_type = models.CharField(
        max_length=20,
        choices=[(t.value, t.value) for t in PaymentMethodType],
    )
    name = models.CharField(max_length=100)
    instructions = models.TextField(blank=True, default="")
    qr_image = models.ImageField(upload_to=payment_qr_upload_to, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments_store_payment_method"
        verbose_name = "método de pago"
        verbose_name_plural = "métodos de pago"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return f"{self.store.name} — {self.name}"
