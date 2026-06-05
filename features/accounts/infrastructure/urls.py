from django.urls import path

from features.accounts.infrastructure.views import AdminDashboardView, LoginView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="accounts-register"),
    path("login/", LoginView.as_view(), name="accounts-login"),
    path("admin/dashboard/", AdminDashboardView.as_view(), name="accounts-admin-dashboard"),
]
