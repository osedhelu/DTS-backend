from features.accounts.domain.entities import UserRole
from features.orders.domain.entities import Order, OrderItem
from features.orders.domain.value_objects import OrderStatus
from features.orders.infrastructure.models import Order as OrderModel
from features.orders.infrastructure.models import OrderItem as OrderItemModel


def _order_to_entity(model: OrderModel) -> Order:
    return Order(
        id=model.id,
        customer_id=model.customer_id,
        store_id=model.store_id,
        driver_id=model.driver_id,
        status=OrderStatus(model.status),
        items=[
            OrderItem(
                id=item.id,
                product_id=item.product_id,
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
