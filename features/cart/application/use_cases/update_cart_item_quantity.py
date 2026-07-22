from django.db import transaction

from features.cart.application.dto import UpdateCartItemQuantityDTO
from features.cart.domain.exceptions import CartItemNotFoundError
from features.cart.infrastructure.models import Cart, CartItem


class UpdateCartItemQuantityUseCase:
    @transaction.atomic
    def execute(self, dto: UpdateCartItemQuantityDTO) -> Cart:
        try:
            cart = Cart.objects.select_for_update().get(user_id=dto.customer_id)
        except Cart.DoesNotExist as exc:
            raise CartItemNotFoundError("Carrito vacío") from exc

        try:
            item = CartItem.objects.select_for_update().get(
                cart=cart,
                product_id=dto.product_id,
            )
        except CartItem.DoesNotExist as exc:
            raise CartItemNotFoundError("Ítem no encontrado en el carrito") from exc

        if dto.quantity <= 0:
            item.delete()
            if not cart.items.exists():
                cart.store = None
                cart.save(update_fields=["store", "updated_at"])
            return cart

        item.quantity = dto.quantity
        item.save(update_fields=["quantity", "updated_at"])
        return cart
