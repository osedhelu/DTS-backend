from features.cart.infrastructure.models import Cart


class GetCartUseCase:
    def execute(self, customer_id: int) -> Cart | None:
        return (
            Cart.objects.filter(user_id=customer_id)
            .select_related("store")
            .prefetch_related("items__product")
            .first()
        )
