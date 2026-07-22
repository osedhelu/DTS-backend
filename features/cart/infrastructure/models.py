from django.conf import settings
from django.db import models

from features.products.infrastructure.models import Product
from features.stores.infrastructure.models import Store


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="customer_carts",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cart_cart"
        verbose_name = "carrito"
        verbose_name_plural = "carritos"

    def __str__(self) -> str:
        return f"Cart user={self.user_id} store={self.store_id}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cart_cart_item"
        verbose_name = "ítem de carrito"
        verbose_name_plural = "ítems de carrito"
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_cart_product",
            ),
        ]

    def __str__(self) -> str:
        return f"CartItem cart={self.cart_id} product={self.product_id} x{self.quantity}"
