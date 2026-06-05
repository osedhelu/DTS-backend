from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from features.analytics.domain.exceptions import InvalidDailyReportError


@dataclass(frozen=True, slots=True)
class CompletedOrderSnapshot:
    """Pedido completado usado como entrada para agregación diaria."""

    store_id: int
    total: Decimal
    completed_on: date
    driver_id: int | None = None
    order_id: int | None = None

    def __post_init__(self) -> None:
        if self.total < 0:
            raise InvalidDailyReportError(
                f"El total del pedido no puede ser negativo: {self.total}"
            )


@dataclass(frozen=True, slots=True)
class StoreSalesSummary:
    store_id: int
    order_count: int
    gross_revenue: Decimal


@dataclass(frozen=True, slots=True)
class DriverCommissionSummary:
    driver_id: int
    delivery_count: int
    commission_amount: Decimal


@dataclass
class DailyReport:
    report_date: date
    store_sales: list[StoreSalesSummary] = field(default_factory=list)
    driver_commissions: list[DriverCommissionSummary] = field(default_factory=list)

    def __post_init__(self) -> None:
        if any(summary.order_count <= 0 for summary in self.store_sales):
            raise InvalidDailyReportError(
                "Cada resumen de tienda debe tener al menos un pedido"
            )
        if any(summary.delivery_count <= 0 for summary in self.driver_commissions):
            raise InvalidDailyReportError(
                "Cada comisión de conductor debe tener al menos una entrega"
            )

    @property
    def total_revenue(self) -> Decimal:
        return sum((summary.gross_revenue for summary in self.store_sales), Decimal("0"))

    @property
    def total_orders(self) -> int:
        return sum(summary.order_count for summary in self.store_sales)

    @property
    def total_driver_commissions(self) -> Decimal:
        return sum(
            (summary.commission_amount for summary in self.driver_commissions),
            Decimal("0"),
        )
