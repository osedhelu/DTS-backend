from django.urls import path

from features.delivery.infrastructure.views import OrderTrackingView

urlpatterns = [
    path(
        "<int:order_id>/tracking/",
        OrderTrackingView.as_view(),
        name="order-tracking",
    ),
]
