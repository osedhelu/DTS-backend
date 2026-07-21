from django.urls import path

from features.payments.infrastructure.views import (
    OrderConfirmPaymentView,
    StorePaymentMethodDetailView,
    StorePaymentMethodListView,
)

urlpatterns = [
    path(
        "stores/<int:store_id>/payment-methods/",
        StorePaymentMethodListView.as_view(),
        name="store-payment-methods",
    ),
    path(
        "stores/<int:store_id>/payment-methods/<int:method_id>/",
        StorePaymentMethodDetailView.as_view(),
        name="store-payment-method-detail",
    ),
    path(
        "orders/<int:order_id>/confirm-payment/",
        OrderConfirmPaymentView.as_view(),
        name="order-confirm-payment",
    ),
]
