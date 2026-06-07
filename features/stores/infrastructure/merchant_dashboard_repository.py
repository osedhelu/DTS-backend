from datetime import date, timedelta
from decimal import Decimal

from django.db.models import F, Sum
from django.db.models.functions import Coalesce

from features.orders.domain.value_objects import OrderStatus
from features.orders.infrastructure.models import Order, OrderItem
from features.products.infrastructure.models import Product
from features.stores.domain.dashboard_entities import (
    OrderSalesSnapshot,
    ProductSalesSnapshot,
)

COMPLETED_ORDER_STATUSES = (
    OrderStatus.DELIVERED,
    OrderStatus.COMPLETED,
)


class DjangoMerchantDashboardRepository:
    def get_completed_orders(
        self,
        store_id: int,
        *,
        start_date: date,
        end_date: date,
    ) -> list[OrderSalesSnapshot]:
        orders = Order.objects.filter(
            store_id=store_id,
            status__in=[status.value for status in COMPLETED_ORDER_STATUSES],
            updated_at__date__gte=start_date,
            updated_at__date__lte=end_date,
        )

        return [
            OrderSalesSnapshot(
                order_id=order.id,
                total=order.total,
                completed_on=order.updated_at.date(),
            )
            for order in orders
        ]

    def count_completed_orders_on(
        self,
        store_id: int,
        *,
        start_date: date,
        end_date: date,
    ) -> int:
        return Order.objects.filter(
            store_id=store_id,
            status__in=[status.value for status in COMPLETED_ORDER_STATUSES],
            updated_at__date__gte=start_date,
            updated_at__date__lte=end_date,
        ).count()

    def count_active_products(self, store_id: int) -> int:
        return Product.objects.filter(store_id=store_id, is_active=True).count()

    def get_product_sales(
        self,
        store_id: int,
        *,
        start_date: date,
        end_date: date,
    ) -> list[ProductSalesSnapshot]:
        rows = (
            OrderItem.objects.filter(
                order__store_id=store_id,
                order__status__in=[status.value for status in COMPLETED_ORDER_STATUSES],
                order__updated_at__date__gte=start_date,
                order__updated_at__date__lte=end_date,
            )
            .values("product_id", "product_name")
            .annotate(
                quantity_sold=Sum("quantity"),
                revenue=Coalesce(
                    Sum(F("unit_price") * F("quantity")),
                    Decimal("0"),
                ),
            )
            .order_by("-revenue")
        )

        return [
            ProductSalesSnapshot(
                product_id=row["product_id"],
                product_name=row["product_name"],
                quantity_sold=row["quantity_sold"] or 0,
                revenue=row["revenue"] or Decimal("0"),
            )
            for row in rows
        ]

    @staticmethod
    def resolve_period(days: int, *, period_end: date | None = None) -> tuple[date, date, int]:
        bounded_days = min(max(days, 1), 90)
        end_date = period_end or date.today()
        start_date = end_date - timedelta(days=bounded_days - 1)
        return start_date, end_date, bounded_days

    @staticmethod
    def week_start(reference: date) -> date:
        return reference - timedelta(days=reference.weekday())
