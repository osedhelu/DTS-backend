from datetime import date

from features.analytics.domain.entities import CompletedOrderSnapshot
from features.orders.domain.value_objects import OrderStatus
from features.orders.infrastructure.models import Order

COMPLETED_ORDER_STATUSES = (
    OrderStatus.DELIVERED,
    OrderStatus.COMPLETED,
)


class DjangoCompletedOrderSource:
    def list_completed_on(self, report_date: date) -> list[CompletedOrderSnapshot]:
        orders = Order.objects.filter(
            status__in=[status.value for status in COMPLETED_ORDER_STATUSES],
            updated_at__date=report_date,
        )

        return [
            CompletedOrderSnapshot(
                order_id=order.id,
                store_id=order.store_id,
                driver_id=order.driver_id,
                total=order.total,
                completed_on=report_date,
            )
            for order in orders
        ]
