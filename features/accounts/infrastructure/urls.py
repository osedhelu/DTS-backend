from django.urls import path

from features.accounts.infrastructure.admin_map_views import AdminOperationsMapView
from features.accounts.infrastructure.admin_merchant_views import AdminMerchantListView
from features.accounts.infrastructure.views import (
    AdminDashboardView,
    DeviceTokenView,
    DriverAvailabilityView,
    LoginView,
    MerchantRegisterView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshView,
    RegisterView,
    ResendVerificationView,
    VerifyEmailView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="accounts-register"),
    path("merchant/register/", MerchantRegisterView.as_view(), name="accounts-merchant-register"),
    path("verify-email/", VerifyEmailView.as_view(), name="accounts-verify-email"),
    path(
        "resend-verification/",
        ResendVerificationView.as_view(),
        name="accounts-resend-verification",
    ),
    path("login/", LoginView.as_view(), name="accounts-login"),
    path(
        "password-reset/request/",
        PasswordResetRequestView.as_view(),
        name="accounts-password-reset-request",
    ),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="accounts-password-reset-confirm",
    ),
    path("refresh/", RefreshView.as_view(), name="accounts-refresh"),
    path("device-token/", DeviceTokenView.as_view(), name="accounts-device-token"),
    path(
        "driver/availability/",
        DriverAvailabilityView.as_view(),
        name="accounts-driver-availability",
    ),
    path("admin/dashboard/", AdminDashboardView.as_view(), name="accounts-admin-dashboard"),
    path("admin/merchants/", AdminMerchantListView.as_view(), name="accounts-admin-merchants"),
    path("admin/map/", AdminOperationsMapView.as_view(), name="accounts-admin-map"),
]
