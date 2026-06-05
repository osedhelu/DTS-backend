from datetime import date

from celery import shared_task

from features.analytics.application.use_cases.calculate_daily_stats import (
    CalculateDailyStatsUseCase,
)


def _build_calculate_daily_stats_use_case() -> CalculateDailyStatsUseCase:
    from features.analytics.infrastructure.completed_orders import DjangoCompletedOrderSource
    from features.analytics.infrastructure.repositories import DjangoDailyReportRepository

    return CalculateDailyStatsUseCase(
        completed_order_source=DjangoCompletedOrderSource(),
        report_repository=DjangoDailyReportRepository(),
    )


def execute_calculate_daily_stats(report_date: date | None = None) -> str:
    use_case = _build_calculate_daily_stats_use_case()
    return use_case.execute(report_date)


@shared_task(name="features.analytics.infrastructure.tasks.calculate_daily_stats")
def calculate_daily_stats(report_date: str | None = None) -> str:
    parsed_date = date.fromisoformat(report_date) if report_date else None
    return execute_calculate_daily_stats(parsed_date)
