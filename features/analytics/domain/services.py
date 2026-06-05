from collections import defaultdict
from datetime import date
from decimal import Decimal

from features.analytics.domain.entities import (
    CompletedOrderSnapshot,
    DailyReport,
    DriverCommissionSummary,
    StoreSalesSummary,
)

DEFAULT_DRIVER_COMMISSION_RATE = Decimal("0.10")


class DailyReportAggregator:
    @staticmethod
    def aggregate(
        report_date: date,
        orders: list[CompletedOrderSnapshot],
        driver_commission_rate: Decimal = DEFAULT_DRIVER_COMMISSION_RATE,
    ) -> DailyReport:
        day_orders = [order for order in orders if order.completed_on == report_date]
        if not day_orders:
            return DailyReport(report_date=report_date)

        store_stats: dict[int, tuple[int, Decimal]] = defaultdict(
            lambda: (0, Decimal("0"))
        )
        driver_stats: dict[int, tuple[int, Decimal]] = defaultdict(
            lambda: (0, Decimal("0"))
        )

        for order in day_orders:
            order_count, revenue = store_stats[order.store_id]
            store_stats[order.store_id] = (
                order_count + 1,
                revenue + order.total,
            )

            if order.driver_id is None:
                continue

            delivery_count, commission_total = driver_stats[order.driver_id]
            order_commission = (order.total * driver_commission_rate).quantize(
                Decimal("0.01")
            )
            driver_stats[order.driver_id] = (
                delivery_count + 1,
                commission_total + order_commission,
            )

        store_sales = [
            StoreSalesSummary(
                store_id=store_id,
                order_count=order_count,
                gross_revenue=revenue,
            )
            for store_id, (order_count, revenue) in sorted(store_stats.items())
        ]
        driver_commissions = [
            DriverCommissionSummary(
                driver_id=driver_id,
                delivery_count=delivery_count,
                commission_amount=commission_amount,
            )
            for driver_id, (delivery_count, commission_amount) in sorted(
                driver_stats.items()
            )
        ]

        return DailyReport(
            report_date=report_date,
            store_sales=store_sales,
            driver_commissions=driver_commissions,
        )
