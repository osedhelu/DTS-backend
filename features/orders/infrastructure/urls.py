from django.urls import path

from features.orders.infrastructure.views import (
    OrderDetailView,
    OrderListCreateView,
    ServiceOrderCreateView,
)

urlpatterns = [
    path("", OrderListCreateView.as_view(), name="orders-list-create"),
    path("service/", ServiceOrderCreateView.as_view(), name="orders-service-create"),
    path("<int:order_id>/", OrderDetailView.as_view(), name="orders-detail"),
]
