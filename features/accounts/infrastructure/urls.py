from django.urls import path

from features.accounts.infrastructure.views import LoginView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="accounts-register"),
    path("login/", LoginView.as_view(), name="accounts-login"),
]
