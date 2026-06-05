from django.urls import path

from features.orders.infrastructure.views import OrderDetailView, OrderListCreateView

urlpatterns = [
    path("", OrderListCreateView.as_view(), name="orders-list-create"),
    path("<int:order_id>/", OrderDetailView.as_view(), name="orders-detail"),
]
