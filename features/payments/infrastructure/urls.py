from django.urls import path

from features.payments.infrastructure.sandbox_views import (
    OrderSandboxPayView,
    PaymentSandboxConfigView,
)
from features.payments.infrastructure.views import (
    OrderConfirmPaymentView,
    StorePaymentMethodDetailView,
    StorePaymentMethodListView,
)

urlpatterns = [
    path(
        "sandbox-config/",
        PaymentSandboxConfigView.as_view(),
        name="payment-sandbox-config",
    ),
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
    path(
        "orders/<int:order_id>/sandbox-pay/",
        OrderSandboxPayView.as_view(),
        name="order-sandbox-pay",
    ),
]
