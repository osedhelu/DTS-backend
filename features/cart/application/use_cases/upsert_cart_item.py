from django.db import transaction

from features.cart.application.dto import UpsertCartItemDTO
from features.cart.domain.exceptions import CartProductNotFoundError, CartStoreConflictError
from features.cart.infrastructure.models import Cart, CartItem
from features.products.infrastructure.models import Product


class UpsertCartItemUseCase:
    @transaction.atomic
    def execute(self, dto: UpsertCartItemDTO) -> Cart:
        try:
            product = Product.objects.select_related("store").get(
                pk=dto.product_id,
                is_active=True,
            )
        except Product.DoesNotExist as exc:
            raise CartProductNotFoundError(f"Producto {dto.product_id} no encontrado") from exc

        if dto.quantity <= 0:
            cart, _ = Cart.objects.get_or_create(user_id=dto.customer_id)
            CartItem.objects.filter(cart=cart, product_id=dto.product_id).delete()
            if not cart.items.exists():
                cart.store = None
                cart.save(update_fields=["store", "updated_at"])
            return cart

        cart, _ = Cart.objects.select_for_update().get_or_create(user_id=dto.customer_id)

        if cart.store_id is not None and cart.store_id != product.store_id:
            if not dto.replace_store:
                raise CartStoreConflictError("El carrito pertenece a otro comercio")
            cart.items.all().delete()

        cart.store = product.store
        cart.save(update_fields=["store", "updated_at"])

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": dto.quantity, "notes": dto.notes.strip()},
        )
        if not created:
            item.quantity = dto.quantity
            if dto.notes is not None:
                item.notes = dto.notes.strip()
            item.save(update_fields=["quantity", "notes", "updated_at"])

        return cart
