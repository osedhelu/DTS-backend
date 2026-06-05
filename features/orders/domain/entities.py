from dataclasses import dataclass, field
from decimal import Decimal

from features.orders.domain.exceptions import InvalidOrderItemError
from features.orders.domain.value_objects import OrderStatus, OrderType, ServiceOrderDetails


@dataclass
class OrderItem:
    product_id: int
    product_name: str
    unit_price: Decimal
    quantity: int
    id: int | None = None

    def __post_init__(self) -> None:
        if self.unit_price <= 0:
            raise InvalidOrderItemError(
                f"El precio unitario debe ser positivo, recibido: {self.unit_price}"
            )
        if self.quantity <= 0:
            raise InvalidOrderItemError(
                f"La cantidad debe ser positiva, recibida: {self.quantity}"
            )

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class Order:
    customer_id: int
    store_id: int
    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.CREATED
    order_type: OrderType = OrderType.DELIVERY
    driver_id: int | None = None
    service_details: ServiceOrderDetails | None = None
    id: int | None = None

    @property
    def is_service(self) -> bool:
        return self.order_type == OrderType.SERVICE

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0"))

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)
