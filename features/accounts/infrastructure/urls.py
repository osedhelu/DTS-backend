from django.urls import path

from features.accounts.infrastructure.views import (
    AdminDashboardView,
    DeviceTokenView,
    LoginView,
    MerchantRegisterView,
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
    path("device-token/", DeviceTokenView.as_view(), name="accounts-device-token"),
    path("admin/dashboard/", AdminDashboardView.as_view(), name="accounts-admin-dashboard"),
]
