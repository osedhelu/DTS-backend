from django.urls import include, path

ACCOUNTS_URLCONF = "features.accounts.tests.urls"

urlpatterns = [
    path("api/v1/accounts/", include("features.accounts.infrastructure.urls")),
]
