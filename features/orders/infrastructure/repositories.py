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
        payment_status=model.payment_status,
        payment_method_id=model.payment_method_id,
        payment_reference=model.payment_reference,
        paid_at=model.paid_at,
        coupon_code=model.coupon_code,
        discount_amount=model.discount_amount,
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
            payment_method_id=data.get("payment_method_id"),
            payment_status=data.get("payment_status", "pending"),
            coupon_code=data.get("coupon_code", ""),
            discount_amount=data.get("discount_amount", 0),
            payment_reference=data.get("payment_reference", ""),
        )
        for item in data["items"]:
            OrderItemModel.objects.create(
                order=order,
                product_id=item["product_id"],
                product_name=item["product_name"],
                unit_price=item["unit_price"],
                quantity=item["quantity"],
            )

        order.total = order.compute_total() - order.discount_amount
        if order.total < 0:
            order.total = 0
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

    def assign_driver(self, order_id: int, driver_id: int) -> Order:
        model = OrderModel.objects.get(pk=order_id)
        model.driver_id = driver_id
        model.save(update_fields=["driver_id", "updated_at"])
        model = OrderModel.objects.prefetch_related("items").get(pk=order_id)
        return _order_to_entity(model)

    def list_for_user(
        self,
        user_id: int,
        role: UserRole,
        status: OrderStatus | None = None,
    ) -> list[Order]:
        return [
            _order_to_entity(model)
            for model in self.list_models_for_user(user_id, role, status=status)
        ]

    def list_models_for_user(
        self,
        user_id: int,
        role: UserRole,
        status: OrderStatus | None = None,
    ) -> list[OrderModel]:
        queryset = (
            OrderModel.objects.select_related(
                "store",
                "customer__customer_profile",
                "driver__driver_profile",
                "payment_method",
            )
            .prefetch_related("items")
            .order_by("-created_at")
        )

        if role == UserRole.CUSTOMER:
            queryset = queryset.filter(customer_id=user_id)
        elif role == UserRole.MERCHANT:
            queryset = queryset.filter(store__owner_id=user_id)
        elif role == UserRole.DRIVER:
            queryset = queryset.filter(driver_id=user_id)
        else:
            return []

        if status is not None:
            queryset = queryset.filter(status=status.value)

        return list(queryset)
