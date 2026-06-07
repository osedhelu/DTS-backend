from datetime import date
from decimal import Decimal

from features.stores.domain.dashboard_entities import OrderSalesSnapshot, ProductSalesSnapshot
from features.stores.domain.dashboard_services import MerchantDashboardAggregator


def test_merchant_dashboard_aggregation():
    period_end = date(2026, 6, 5)
    completed_orders = [
        OrderSalesSnapshot(order_id=1, total=Decimal("100000.00"), completed_on=date(2026, 6, 1)),
        OrderSalesSnapshot(order_id=2, total=Decimal("50000.00"), completed_on=date(2026, 6, 1)),
        OrderSalesSnapshot(order_id=3, total=Decimal("80000.00"), completed_on=date(2026, 6, 5)),
    ]
    product_sales = [
        ProductSalesSnapshot(
            product_id=10,
            product_name="Hamburguesa",
            quantity_sold=12,
            revenue=Decimal("180000.00"),
        ),
        ProductSalesSnapshot(
            product_id=11,
            product_name="Papas",
            quantity_sold=20,
            revenue=Decimal("50000.00"),
        ),
    ]

    metrics = MerchantDashboardAggregator.aggregate(
        store_id=1,
        period_days=7,
        period_end=period_end,
        completed_orders=completed_orders,
        orders_today=1,
        orders_this_week=3,
        active_products=8,
        product_sales=product_sales,
    )

    assert metrics.total_sales == Decimal("230000.00")
    assert metrics.order_count == 3
    assert metrics.orders_today == 1
    assert metrics.orders_this_week == 3
    assert metrics.average_ticket == Decimal("76666.67")
    assert metrics.platform_commission == Decimal("34500.00")
    assert metrics.net_earnings == Decimal("195500.00")
    assert metrics.active_products == 8
    assert len(metrics.sales_series) == 7
    assert metrics.sales_series[0].date == date(2026, 5, 30)
    assert metrics.sales_series[0].total == Decimal("0")
    assert metrics.sales_series[2].total == Decimal("150000.00")
    assert metrics.top_products[0].product_name == "Hamburguesa"
    assert metrics.top_products[0].revenue == Decimal("180000.00")
