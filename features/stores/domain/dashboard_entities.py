from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


DEFAULT_PLATFORM_COMMISSION_RATE = Decimal("0.15")


@dataclass(frozen=True)
class OrderSalesSnapshot:
    order_id: int
    total: Decimal
    completed_on: date


@dataclass(frozen=True)
class ProductSalesSnapshot:
    product_id: int | None
    product_name: str
    quantity_sold: int
    revenue: Decimal


@dataclass(frozen=True)
class SalesSeriesPoint:
    date: date
    total: Decimal


@dataclass(frozen=True)
class TopProductSummary:
    product_id: int | None
    product_name: str
    quantity_sold: int
    revenue: Decimal


@dataclass(frozen=True)
class MerchantDashboardMetrics:
    store_id: int
    period_days: int
    total_sales: Decimal
    order_count: int
    orders_today: int
    orders_this_week: int
    average_ticket: Decimal
    platform_commission_rate: Decimal
    platform_commission: Decimal
    net_earnings: Decimal
    active_products: int
    sales_series: list[SalesSeriesPoint] = field(default_factory=list)
    top_products: list[TopProductSummary] = field(default_factory=list)
