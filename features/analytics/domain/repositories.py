from datetime import date
from typing import Protocol

from features.analytics.domain.entities import CompletedOrderSnapshot, DailyReport


class CompletedOrderSource(Protocol):
    def list_completed_on(self, report_date: date) -> list[CompletedOrderSnapshot]: ...


class DailyReportRepository(Protocol):
    def save(self, report: DailyReport) -> DailyReport: ...

    def get_by_date(self, report_date: date) -> DailyReport | None: ...
