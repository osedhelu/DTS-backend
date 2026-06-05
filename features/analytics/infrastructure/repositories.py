from datetime import date

from django.db import transaction

from features.analytics.domain.entities import (
    DailyReport,
    DriverCommissionSummary,
    StoreSalesSummary,
)
from features.analytics.infrastructure.models import DailySalesReport, DriverCommission


class DjangoDailyReportRepository:
    @transaction.atomic
    def save(self, report: DailyReport) -> DailyReport:
        DailySalesReport.objects.filter(report_date=report.report_date).delete()
        DriverCommission.objects.filter(report_date=report.report_date).delete()

        for summary in report.store_sales:
            DailySalesReport.objects.create(
                report_date=report.report_date,
                store_id=summary.store_id,
                order_count=summary.order_count,
                gross_revenue=summary.gross_revenue,
            )

        for summary in report.driver_commissions:
            DriverCommission.objects.create(
                report_date=report.report_date,
                driver_id=summary.driver_id,
                delivery_count=summary.delivery_count,
                commission_amount=summary.commission_amount,
            )

        return report

    def get_by_date(self, report_date: date) -> DailyReport | None:
        store_rows = DailySalesReport.objects.filter(report_date=report_date).order_by(
            "store_id"
        )
        driver_rows = DriverCommission.objects.filter(report_date=report_date).order_by(
            "driver_id"
        )

        if not store_rows.exists() and not driver_rows.exists():
            return None

        return DailyReport(
            report_date=report_date,
            store_sales=[
                StoreSalesSummary(
                    store_id=row.store_id,
                    order_count=row.order_count,
                    gross_revenue=row.gross_revenue,
                )
                for row in store_rows
            ],
            driver_commissions=[
                DriverCommissionSummary(
                    driver_id=row.driver_id,
                    delivery_count=row.delivery_count,
                    commission_amount=row.commission_amount,
                )
                for row in driver_rows
            ],
        )
