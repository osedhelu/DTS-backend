import csv
import io
from datetime import date, timedelta

from django.db.models import Avg, DurationField, ExpressionWrapper, F, Sum
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from features.accounts.infrastructure.permissions import IsSuperAdmin
from features.analytics.infrastructure.models import DailySalesReport, DriverCommission
from features.orders.domain.value_objects import OrderStatus, OrderType
from features.orders.infrastructure.models import Order
from features.stores.domain.entities import StoreStatus
from features.stores.infrastructure.models import Store


def _commissions_date_range(query_params) -> tuple[date, date]:
    days = min(max(int(query_params.get("days", 30)), 1), 90)
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    return start_date, end_date


def _store_sales_rows(start_date: date, end_date: date) -> list[dict]:
    rows = (
        DailySalesReport.objects.filter(
            report_date__gte=start_date,
            report_date__lte=end_date,
        )
        .select_related("store")
        .order_by("report_date", "store_id")
    )
    return [
        {
            "report_date": row.report_date.isoformat(),
            "store_id": row.store_id,
            "store_name": row.store.name,
            "order_count": row.order_count,
            "gross_revenue": str(row.gross_revenue),
        }
        for row in rows
    ]


def _driver_commission_rows(start_date: date, end_date: date) -> list[dict]:
    rows = (
        DriverCommission.objects.filter(
            report_date__gte=start_date,
            report_date__lte=end_date,
        )
        .select_related("driver")
        .order_by("report_date", "driver_id")
    )
    return [
        {
            "report_date": row.report_date.isoformat(),
            "driver_id": row.driver_id,
            "driver_username": row.driver.username,
            "driver_email": row.driver.email,
            "delivery_count": row.delivery_count,
            "commission_amount": str(row.commission_amount),
        }
        for row in rows
    ]


@extend_schema_view(
    get=extend_schema(
        responses={
            200: inline_serializer(
                name="AdminMetrics",
                fields={
                    "sales_series": serializers.ListField(
                        child=inline_serializer(
                            name="SalesSeriesPoint",
                            fields={
                                "date": serializers.DateField(),
                                "total": serializers.DecimalField(
                                    max_digits=14,
                                    decimal_places=2,
                                ),
                            },
                        )
                    ),
                    "active_stores": serializers.IntegerField(),
                    "average_delivery_minutes": serializers.FloatField(
                        allow_null=True
                    ),
                },
            )
        }
    )
)
class AdminMetricsView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        days = min(max(int(request.query_params.get("days", 7)), 1), 30)
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        sales_by_date = {
            row["report_date"]: row["total"]
            for row in DailySalesReport.objects.filter(
                report_date__gte=start_date,
                report_date__lte=end_date,
            )
            .values("report_date")
            .annotate(total=Sum("gross_revenue"))
            .order_by("report_date")
        }

        sales_series = [
            {
                "date": current.isoformat(),
                "total": str(sales_by_date.get(current, 0)),
            }
            for current in (
                start_date + timedelta(days=offset) for offset in range(days)
            )
        ]

        active_stores = Store.objects.filter(status=StoreStatus.OPEN.value).count()

        delivered_orders = Order.objects.filter(
            status=OrderStatus.DELIVERED.value,
            order_type=OrderType.DELIVERY.value,
            updated_at__date__gte=start_date,
        )
        average_delivery = delivered_orders.aggregate(
            avg_duration=Avg(
                ExpressionWrapper(
                    F("updated_at") - F("created_at"),
                    output_field=DurationField(),
                )
            )
        )["avg_duration"]
        average_delivery_minutes = (
            round(average_delivery.total_seconds() / 60, 1)
            if average_delivery is not None
            else None
        )

        return Response(
            {
                "sales_series": sales_series,
                "active_stores": active_stores,
                "average_delivery_minutes": average_delivery_minutes,
            }
        )


@extend_schema_view(
    get=extend_schema(
        responses={
            200: inline_serializer(
                name="AdminCommissions",
                fields={
                    "store_sales": serializers.ListField(
                        child=inline_serializer(
                            name="StoreSalesRow",
                            fields={
                                "report_date": serializers.DateField(),
                                "store_id": serializers.IntegerField(),
                                "store_name": serializers.CharField(),
                                "order_count": serializers.IntegerField(),
                                "gross_revenue": serializers.DecimalField(
                                    max_digits=14,
                                    decimal_places=2,
                                ),
                            },
                        )
                    ),
                    "driver_commissions": serializers.ListField(
                        child=inline_serializer(
                            name="DriverCommissionRow",
                            fields={
                                "report_date": serializers.DateField(),
                                "driver_id": serializers.IntegerField(),
                                "driver_username": serializers.CharField(),
                                "driver_email": serializers.EmailField(),
                                "delivery_count": serializers.IntegerField(),
                                "commission_amount": serializers.DecimalField(
                                    max_digits=14,
                                    decimal_places=2,
                                ),
                            },
                        )
                    ),
                },
            )
        }
    )
)
class AdminCommissionsListView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        start_date, end_date = _commissions_date_range(request.query_params)
        return Response(
            {
                "store_sales": _store_sales_rows(start_date, end_date),
                "driver_commissions": _driver_commission_rows(start_date, end_date),
            }
        )


@extend_schema_view(
    get=extend_schema(
        responses={
            200: inline_serializer(
                name="AdminCommissionsExport",
                fields={
                    "content": serializers.CharField(),
                },
            )
        }
    )
)
class AdminCommissionsExportView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        start_date, end_date = _commissions_date_range(request.query_params)
        store_sales = _store_sales_rows(start_date, end_date)
        driver_commissions = _driver_commission_rows(start_date, end_date)

        buffer = io.StringIO()
        writer = csv.writer(buffer)

        writer.writerow(["Ventas por comercio"])
        writer.writerow(
            [
                "report_date",
                "store_id",
                "store_name",
                "order_count",
                "gross_revenue",
            ]
        )
        for row in store_sales:
            writer.writerow(
                [
                    row["report_date"],
                    row["store_id"],
                    row["store_name"],
                    row["order_count"],
                    row["gross_revenue"],
                ]
            )

        writer.writerow([])
        writer.writerow(["Comisiones por conductor"])
        writer.writerow(
            [
                "report_date",
                "driver_id",
                "driver_username",
                "driver_email",
                "delivery_count",
                "commission_amount",
            ]
        )
        for row in driver_commissions:
            writer.writerow(
                [
                    row["report_date"],
                    row["driver_id"],
                    row["driver_username"],
                    row["driver_email"],
                    row["delivery_count"],
                    row["commission_amount"],
                ]
            )

        response = HttpResponse(buffer.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="commissions_report.csv"'
        )
        return response
