from django.db import models

from features.accounts.infrastructure.models import CustomUser
from features.stores.infrastructure.models import Store


class DailySalesReport(models.Model):
    report_date = models.DateField()
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="daily_sales_reports",
    )
    order_count = models.PositiveIntegerField()
    gross_revenue = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analytics_daily_sales_report"
        verbose_name = "reporte diario de ventas"
        verbose_name_plural = "reportes diarios de ventas"
        constraints = [
            models.UniqueConstraint(
                fields=["report_date", "store"],
                name="uniq_analytics_daily_sales_report_store_date",
            )
        ]
        ordering = ["report_date", "store_id"]

    def __str__(self) -> str:
        return f"Ventas {self.report_date} — tienda #{self.store_id}"


class DriverCommission(models.Model):
    report_date = models.DateField()
    driver = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="driver_commissions",
    )
    delivery_count = models.PositiveIntegerField()
    commission_amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analytics_driver_commission"
        verbose_name = "comisión diaria de conductor"
        verbose_name_plural = "comisiones diarias de conductor"
        constraints = [
            models.UniqueConstraint(
                fields=["report_date", "driver"],
                name="uniq_analytics_driver_commission_driver_date",
            )
        ]
        ordering = ["report_date", "driver_id"]

    def __str__(self) -> str:
        return f"Comisión {self.report_date} — conductor #{self.driver_id}"
