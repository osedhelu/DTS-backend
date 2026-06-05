from features.accounts.domain.entities import UserRole
from features.orders.domain.entities import Order, OrderItem
from features.orders.domain.value_objects import OrderStatus, OrderType, ServiceOrderDetails
from features.orders.infrastructure.models import Order as OrderModel
from features.orders.infrastructure.models import OrderItem as OrderItemModel


def _build_service_details(model: OrderModel) -> ServiceOrderDetails | None:
    if model.order_type != OrderType.SERVICE:
        return None
    if not model.service_address:
        return None
    return ServiceOrderDetails(
        service_address=model.service_address,
        customer_notes=model.customer_notes,
        scheduled_at=model.scheduled_at,
        latitude=model.service_latitude,
        longitude=model.service_longitude,
        duration_minutes=model.duration_minutes,
    )


def _order_to_entity(model: OrderModel) -> Order:
    return Order(
        id=model.id,
        customer_id=model.customer_id,
        store_id=model.store_id,
        driver_id=model.driver_id,
        status=OrderStatus(model.status),
        order_type=OrderType(model.order_type),
        service_details=_build_service_details(model),
        items=[
            OrderItem(
                id=item.id,
                product_id=item.product_id or 0,
                product_name=item.product_name,
                unit_price=item.unit_price,
                quantity=item.quantity,
            )
            for item in model.items.all()
        ],
    )


class DjangoOrderRepository:
    def create(self, data: dict) -> Order:
        order = OrderModel.objects.create(
            customer_id=data["customer_id"],
            store_id=data["store_id"],
            status=data["status"],
            order_type=data.get("order_type", OrderType.DELIVERY),
            service_address=data.get("service_address", ""),
            customer_notes=data.get("customer_notes", ""),
            scheduled_at=data.get("scheduled_at"),
            service_latitude=data.get("service_latitude"),
            service_longitude=data.get("service_longitude"),
            duration_minutes=data.get("duration_minutes"),
        )
        for item in data["items"]:
            OrderItemModel.objects.create(
                order=order,
                product_id=item["product_id"],
                product_name=item["product_name"],
                unit_price=item["unit_price"],
                quantity=item["quantity"],
            )

        order.total = order.compute_total()
        order.save(update_fields=["total", "updated_at"])

        order = OrderModel.objects.prefetch_related("items").get(pk=order.pk)
        return _order_to_entity(order)

    def get_by_id(self, order_id: int) -> Order | None:
        try:
            model = OrderModel.objects.prefetch_related("items").get(pk=order_id)
        except OrderModel.DoesNotExist:
            return None
        return _order_to_entity(model)

    def update_status(self, order_id: int, status: OrderStatus) -> Order:
        model = OrderModel.objects.get(pk=order_id)
        model.status = status
        model.save(update_fields=["status", "updated_at"])
        model = OrderModel.objects.prefetch_related("items").get(pk=order_id)
        return _order_to_entity(model)

    def list_for_user(self, user_id: int, role: UserRole) -> list[Order]:
        queryset = OrderModel.objects.prefetch_related("items").order_by("-created_at")

        if role == UserRole.CUSTOMER:
            queryset = queryset.filter(customer_id=user_id)
        elif role == UserRole.MERCHANT:
            queryset = queryset.filter(store__owner_id=user_id)
        elif role == UserRole.DRIVER:
            queryset = queryset.filter(driver_id=user_id)
        else:
            return []

        return [_order_to_entity(model) for model in queryset]
