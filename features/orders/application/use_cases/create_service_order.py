from features.orders.application.dto import CreateServiceOrderDTO
from features.orders.domain.entities import Order, OrderItem
from features.orders.domain.exceptions import EmptyCartError, InvalidServiceOrderError
from features.orders.domain.repositories import OrderRepository
from features.orders.domain.value_objects import OrderStatus, OrderType, ServiceOrderDetails
from features.products.domain.entities import ProductType
from features.products.domain.exceptions import ProductNotFoundError
from features.products.domain.repositories import ProductRepository
from features.stores.domain.exceptions import StoreNotFoundError
from features.stores.domain.repositories import StoreRepository


class CreateServiceOrderUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository: ProductRepository,
        store_repository: StoreRepository,
    ) -> None:
        self._order_repository = order_repository
        self._product_repository = product_repository
        self._store_repository = store_repository

    def execute(self, dto: CreateServiceOrderDTO) -> Order:
        if not dto.items:
            raise EmptyCartError("No se puede crear un pedido sin ítems")

        store = self._store_repository.get_by_id(dto.store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {dto.store_id} no encontrado")

        order_items: list[OrderItem] = []
        duration_minutes: int | None = None

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
            if product.product_type != ProductType.SERVICE:
                raise InvalidServiceOrderError(
                    f"El producto '{product.name}' no es un servicio"
                )

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=line.quantity,
                )
            )

            if product.duration_minutes:
                duration_minutes = max(duration_minutes or 0, product.duration_minutes)

        service_details = ServiceOrderDetails(
            service_address=dto.service_address,
            customer_notes=dto.customer_notes,
            scheduled_at=dto.scheduled_at,
            latitude=dto.latitude,
            longitude=dto.longitude,
            duration_minutes=duration_minutes,
        )

        return self._order_repository.create(
            {
                "customer_id": dto.customer_id,
                "store_id": dto.store_id,
                "status": OrderStatus.CREATED,
                "order_type": OrderType.SERVICE,
                "service_address": service_details.service_address,
                "customer_notes": service_details.customer_notes,
                "scheduled_at": service_details.scheduled_at,
                "service_latitude": service_details.latitude,
                "service_longitude": service_details.longitude,
                "duration_minutes": service_details.duration_minutes,
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
