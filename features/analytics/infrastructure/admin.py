from django.contrib import admin

from features.analytics.infrastructure.models import DailySalesReport, DriverCommission


@admin.register(DailySalesReport)
class DailySalesReportAdmin(admin.ModelAdmin):
    list_display = ("report_date", "store", "order_count", "gross_revenue")
    list_filter = ("report_date",)
    raw_id_fields = ("store",)


@admin.register(DriverCommission)
class DriverCommissionAdmin(admin.ModelAdmin):
    list_display = ("report_date", "driver", "delivery_count", "commission_amount")
    list_filter = ("report_date",)
    raw_id_fields = ("driver",)
