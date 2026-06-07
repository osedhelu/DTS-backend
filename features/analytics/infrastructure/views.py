from datetime import date, timedelta

from django.db.models import Avg, DurationField, ExpressionWrapper, F, Sum
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from features.accounts.infrastructure.permissions import IsSuperAdmin
from features.analytics.infrastructure.models import DailySalesReport
from features.orders.domain.value_objects import OrderStatus, OrderType
from features.orders.infrastructure.models import Order
from features.stores.domain.entities import StoreStatus
from features.stores.infrastructure.models import Store


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
