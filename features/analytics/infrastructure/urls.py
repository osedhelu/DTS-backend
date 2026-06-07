from django.urls import path

from features.analytics.infrastructure.views import AdminMetricsView

urlpatterns = [
    path("metrics/", AdminMetricsView.as_view(), name="analytics-admin-metrics"),
]
