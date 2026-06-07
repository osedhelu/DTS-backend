from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from features.stores.domain.dashboard_entities import (
    DEFAULT_PLATFORM_COMMISSION_RATE,
    MerchantDashboardMetrics,
    OrderSalesSnapshot,
    ProductSalesSnapshot,
    SalesSeriesPoint,
    TopProductSummary,
)


class MerchantDashboardAggregator:
    @staticmethod
    def aggregate(
        *,
        store_id: int,
        period_days: int,
        period_end: date,
        completed_orders: list[OrderSalesSnapshot],
        orders_today: int,
        orders_this_week: int,
        active_products: int,
        product_sales: list[ProductSalesSnapshot],
        platform_commission_rate: Decimal = DEFAULT_PLATFORM_COMMISSION_RATE,
    ) -> MerchantDashboardMetrics:
        total_sales = sum((order.total for order in completed_orders), Decimal("0"))
        order_count = len(completed_orders)
        average_ticket = (
            (total_sales / order_count).quantize(Decimal("0.01"))
            if order_count
            else Decimal("0")
        )
        platform_commission = (total_sales * platform_commission_rate).quantize(
            Decimal("0.01")
        )
        net_earnings = total_sales - platform_commission

        sales_by_date: dict[date, Decimal] = defaultdict(lambda: Decimal("0"))
        for order in completed_orders:
            sales_by_date[order.completed_on] += order.total

        start_date = period_end - timedelta(days=period_days - 1)
        sales_series = [
            SalesSeriesPoint(
                date=current,
                total=sales_by_date.get(current, Decimal("0")),
            )
            for current in (
                start_date + timedelta(days=offset) for offset in range(period_days)
            )
        ]

        top_products = [
            TopProductSummary(
                product_id=item.product_id,
                product_name=item.product_name,
                quantity_sold=item.quantity_sold,
                revenue=item.revenue,
            )
            for item in sorted(product_sales, key=lambda row: row.revenue, reverse=True)[
                :5
            ]
        ]

        return MerchantDashboardMetrics(
            store_id=store_id,
            period_days=period_days,
            total_sales=total_sales,
            order_count=order_count,
            orders_today=orders_today,
            orders_this_week=orders_this_week,
            average_ticket=average_ticket,
            platform_commission_rate=platform_commission_rate,
            platform_commission=platform_commission,
            net_earnings=net_earnings,
            active_products=active_products,
            sales_series=sales_series,
            top_products=top_products,
        )
