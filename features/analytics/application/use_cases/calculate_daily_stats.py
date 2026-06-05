from datetime import date, timedelta

from django.utils import timezone

from features.analytics.domain.repositories import (
    CompletedOrderSource,
    DailyReportRepository,
)
from features.analytics.domain.services import DailyReportAggregator


class CalculateDailyStatsUseCase:
    def __init__(
        self,
        completed_order_source: CompletedOrderSource,
        report_repository: DailyReportRepository,
    ) -> None:
        self._completed_order_source = completed_order_source
        self._report_repository = report_repository

    def execute(self, report_date: date | None = None) -> str:
        target_date = report_date or (timezone.localdate() - timedelta(days=1))
        snapshots = self._completed_order_source.list_completed_on(target_date)
        report = DailyReportAggregator.aggregate(target_date, snapshots)
        self._report_repository.save(report)

        return (
            f"saved:{target_date.isoformat()}:"
            f"{report.total_orders}:"
            f"{report.total_revenue}"
        )
