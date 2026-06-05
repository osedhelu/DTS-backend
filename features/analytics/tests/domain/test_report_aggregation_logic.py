from datetime import date
from decimal import Decimal

import pytest

from features.analytics.domain.entities import CompletedOrderSnapshot
from features.analytics.domain.exceptions import InvalidDailyReportError
from features.analytics.domain.services import DailyReportAggregator


def test_report_aggregation_logic():
    report_date = date(2026, 6, 5)
    orders = [
        CompletedOrderSnapshot(
            order_id=1,
            store_id=10,
            driver_id=100,
            total=Decimal("50000.00"),
            completed_on=report_date,
        ),
        CompletedOrderSnapshot(
            order_id=2,
            store_id=10,
            driver_id=101,
            total=Decimal("30000.00"),
            completed_on=report_date,
        ),
        CompletedOrderSnapshot(
            order_id=3,
            store_id=20,
            driver_id=100,
            total=Decimal("20000.00"),
            completed_on=report_date,
        ),
        CompletedOrderSnapshot(
            order_id=4,
            store_id=20,
            driver_id=None,
            total=Decimal("15000.00"),
            completed_on=date(2026, 6, 4),
        ),
    ]

    report = DailyReportAggregator.aggregate(report_date, orders)

    assert report.report_date == report_date
    assert report.total_orders == 3
    assert report.total_revenue == Decimal("100000.00")

    assert len(report.store_sales) == 2
    store_10 = next(item for item in report.store_sales if item.store_id == 10)
    store_20 = next(item for item in report.store_sales if item.store_id == 20)
    assert store_10.order_count == 2
    assert store_10.gross_revenue == Decimal("80000.00")
    assert store_20.order_count == 1
    assert store_20.gross_revenue == Decimal("20000.00")

    assert len(report.driver_commissions) == 2
    driver_100 = next(item for item in report.driver_commissions if item.driver_id == 100)
    driver_101 = next(item for item in report.driver_commissions if item.driver_id == 101)
    assert driver_100.delivery_count == 2
    assert driver_100.commission_amount == Decimal("7000.00")
    assert driver_101.delivery_count == 1
    assert driver_101.commission_amount == Decimal("3000.00")
    assert report.total_driver_commissions == Decimal("10000.00")


def test_report_aggregation_returns_empty_report_without_orders():
    report = DailyReportAggregator.aggregate(date(2026, 6, 5), [])

    assert report.store_sales == []
    assert report.driver_commissions == []
    assert report.total_orders == 0
    assert report.total_revenue == Decimal("0")
    assert report.total_driver_commissions == Decimal("0")


def test_completed_order_snapshot_rejects_negative_total():
    with pytest.raises(InvalidDailyReportError, match="negativo"):
        CompletedOrderSnapshot(
            store_id=1,
            total=Decimal("-1.00"),
            completed_on=date(2026, 6, 5),
        )
