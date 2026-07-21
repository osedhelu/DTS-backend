from django.urls import path

from features.accounts.infrastructure.extra_views import (
    AdminDriverVerificationView,
    DriverPayoutListView,
    FavoriteStoreDetailView,
    FavoriteStoreListView,
)
from features.accounts.infrastructure.admin_map_views import AdminOperationsMapView
from features.accounts.infrastructure.admin_merchant_views import AdminMerchantListView
from features.accounts.infrastructure.views import (
    AdminDashboardView,
    AppleAuthView,
    CustomerAddressDetailView,
    CustomerAddressListCreateView,
    CustomerProfileView,
    DeviceTokenView,
    DriverAvailabilityView,
    DriverEarningsView,
    DriverProfileView,
    GoogleAuthView,
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
    path("auth/google/", GoogleAuthView.as_view(), name="accounts-google-auth"),
    path("auth/apple/", AppleAuthView.as_view(), name="accounts-apple-auth"),
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
    path(
        "driver/profile/",
        DriverProfileView.as_view(),
        name="accounts-driver-profile",
    ),
    path(
        "driver/earnings/",
        DriverEarningsView.as_view(),
        name="accounts-driver-earnings",
    ),
    path(
        "customer/profile/",
        CustomerProfileView.as_view(),
        name="accounts-customer-profile",
    ),
    path(
        "customer/addresses/",
        CustomerAddressListCreateView.as_view(),
        name="accounts-customer-addresses",
    ),
    path(
        "customer/addresses/<int:address_id>/",
        CustomerAddressDetailView.as_view(),
        name="accounts-customer-address-detail",
    ),
    path("admin/dashboard/", AdminDashboardView.as_view(), name="accounts-admin-dashboard"),
    path("admin/merchants/", AdminMerchantListView.as_view(), name="accounts-admin-merchants"),
    path("admin/map/", AdminOperationsMapView.as_view(), name="accounts-admin-map"),
    path("customer/favorites/", FavoriteStoreListView.as_view(), name="accounts-favorites"),
    path(
        "customer/favorites/<int:store_id>/",
        FavoriteStoreDetailView.as_view(),
        name="accounts-favorite-detail",
    ),
    path("driver/payouts/", DriverPayoutListView.as_view(), name="accounts-driver-payouts"),
    path(
        "admin/drivers/<int:driver_id>/verification/",
        AdminDriverVerificationView.as_view(),
        name="accounts-admin-driver-verification",
    ),
]
