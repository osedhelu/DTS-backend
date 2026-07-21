from django.urls import path

from features.delivery.infrastructure.proof_views import ProofOfDeliveryView
from features.delivery.infrastructure.views import OrderTrackingView

urlpatterns = [
    path(
        "<int:order_id>/tracking/",
        OrderTrackingView.as_view(),
        name="order-tracking",
    ),
    path(
        "<int:order_id>/proof-of-delivery/",
        ProofOfDeliveryView.as_view(),
        name="order-proof-of-delivery",
    ),
]
