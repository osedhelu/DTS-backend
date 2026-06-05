from features.orders.application.dto import CreateOrderDTO
from features.orders.domain.entities import Order, OrderItem
from features.orders.domain.exceptions import EmptyCartError
from features.orders.domain.repositories import OrderRepository
from features.orders.domain.value_objects import OrderStatus
from features.products.domain.exceptions import InsufficientStockError, ProductNotFoundError
from features.products.domain.repositories import ProductRepository
from features.products.domain.services import StockValidator
from features.stores.domain.exceptions import StoreNotFoundError
from features.stores.domain.repositories import StoreRepository


class CreateOrderUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository: ProductRepository,
        store_repository: StoreRepository,
    ) -> None:
        self._order_repository = order_repository
        self._product_repository = product_repository
        self._store_repository = store_repository

    def execute(self, dto: CreateOrderDTO) -> Order:
        if not dto.items:
            raise EmptyCartError("No se puede crear un pedido sin ítems")

        store = self._store_repository.get_by_id(dto.store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {dto.store_id} no encontrado")

        order_items: list[OrderItem] = []
        for line in dto.items:
            product = self._product_repository.get_by_id(line.product_id)
            if product is None or product.store_id != dto.store_id:
                raise ProductNotFoundError(
                    f"Producto {line.product_id} no encontrado en este comercio"
                )
            if not product.is_active:
                raise ProductNotFoundError(
                    f"Producto '{product.name}' no está disponible"
                )

            StockValidator.validate(product, line.quantity)

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=line.quantity,
                )
            )

        return self._order_repository.create(
            {
                "customer_id": dto.customer_id,
                "store_id": dto.store_id,
                "status": OrderStatus.CREATED,
                "items": [
                    {
                        "product_id": item.product_id,
                        "product_name": item.product_name,
                        "unit_price": item.unit_price,
                        "quantity": item.quantity,
                    }
                    for item in order_items
                ],
            }
        )
