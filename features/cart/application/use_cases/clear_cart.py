from django.db import transaction

from features.cart.infrastructure.models import Cart


class ClearCartUseCase:
    @transaction.atomic
    def execute(self, customer_id: int) -> None:
        cart = Cart.objects.filter(user_id=customer_id).first()
        if cart is None:
            return
        cart.items.all().delete()
        cart.store = None
        cart.save(update_fields=["store", "updated_at"])


def clear_customer_cart(customer_id: int) -> None:
    ClearCartUseCase().execute(customer_id)
