from decimal import Decimal

from django.db import models

from features.accounts.infrastructure.models import CustomUser
from features.orders.domain.value_objects import OrderStatus
from features.products.infrastructure.models import Product
from features.stores.infrastructure.models import Store


class Order(models.Model):
    customer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    driver = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_orders",
    )
    status = models.CharField(
        max_length=32,
        choices=[(status.value, status.value) for status in OrderStatus],
        default=OrderStatus.CREATED,
    )
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders_order"
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Pedido #{self.pk} — {self.store.name}"

    def compute_total(self) -> Decimal:
        return sum((item.subtotal for item in self.items.all()), Decimal("0"))


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    product_name = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders_orderitem"
        verbose_name = "ítem de pedido"
        verbose_name_plural = "ítems de pedido"

    def __str__(self) -> str:
        return f"{self.quantity}x {self.product_name}"

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity
