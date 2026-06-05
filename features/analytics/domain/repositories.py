from datetime import date
from typing import Protocol

from features.analytics.domain.entities import DailyReport


class DailyReportRepository(Protocol):
    def save(self, report: DailyReport) -> DailyReport: ...

    def get_by_date(self, report_date: date) -> DailyReport | None: ...
