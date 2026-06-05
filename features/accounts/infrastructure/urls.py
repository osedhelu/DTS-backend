from django.urls import path

from features.accounts.infrastructure.views import (
    AdminDashboardView,
    DeviceTokenView,
    LoginView,
    RegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="accounts-register"),
    path("login/", LoginView.as_view(), name="accounts-login"),
    path("device-token/", DeviceTokenView.as_view(), name="accounts-device-token"),
    path("admin/dashboard/", AdminDashboardView.as_view(), name="accounts-admin-dashboard"),
]
