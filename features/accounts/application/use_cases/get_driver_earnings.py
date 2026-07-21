from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone

from features.accounts.application.dto import DriverEarningBreakdownItem, DriverEarningsResult
from features.accounts.domain.exceptions import InvalidEarningsPeriodError
from features.analytics.domain.services import DEFAULT_DRIVER_COMMISSION_RATE
from features.orders.domain.value_objects import OrderStatus
from features.orders.infrastructure.models import Order

VALID_EARNINGS_PERIODS = frozenset({"today", "week", "month"})


def _period_bounds(period: str, now: datetime) -> tuple[datetime, datetime]:
    local_now = timezone.localtime(now)
    start_of_day = local_now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "today":
        return start_of_day, start_of_day + timedelta(days=1)
    if period == "week":
        week_start = start_of_day - timedelta(days=local_now.weekday())
        return week_start, week_start + timedelta(days=7)
    if period == "month":
        month_start = start_of_day.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        return month_start, month_end

    raise InvalidEarningsPeriodError(
        f"Periodo inválido: {period}. Use today, week o month."
    )


class GetDriverEarningsUseCase:
    def execute(self, driver_id: int, period: str) -> DriverEarningsResult:
        if period not in VALID_EARNINGS_PERIODS:
            raise InvalidEarningsPeriodError(
                f"Periodo inválido: {period}. Use today, week o month."
            )

        start, end = _period_bounds(period, timezone.now())
        orders = Order.objects.filter(
            driver_id=driver_id,
            status=OrderStatus.DELIVERED,
            updated_at__gte=start,
            updated_at__lt=end,
        ).order_by("-updated_at")

        breakdown: list[DriverEarningBreakdownItem] = []
        total_earnings = Decimal("0")

        for order in orders:
            earning = (order.total * DEFAULT_DRIVER_COMMISSION_RATE).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
            total_earnings += earning
            breakdown.append(
                DriverEarningBreakdownItem(
                    order_id=order.id,
                    completed_at=order.updated_at,
                    order_total=order.total,
                    earning=earning,
                )
            )

        return DriverEarningsResult(
            period=period,
            delivery_count=len(breakdown),
            total_earnings=total_earnings.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            ),
            currency="COP",
            breakdown=tuple(breakdown),
        )
