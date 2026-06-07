from django.urls import path

from features.analytics.infrastructure.views import (
    AdminCommissionsExportView,
    AdminCommissionsListView,
    AdminMetricsView,
)

urlpatterns = [
    path("metrics/", AdminMetricsView.as_view(), name="analytics-admin-metrics"),
    path(
        "commissions/",
        AdminCommissionsListView.as_view(),
        name="analytics-admin-commissions",
    ),
    path(
        "commissions/export/",
        AdminCommissionsExportView.as_view(),
        name="analytics-admin-commissions-export",
    ),
]
