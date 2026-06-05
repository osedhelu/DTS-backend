from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status


THROTTLE_SETTINGS = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "core.api.pagination.StandardResultsPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "core.api.throttling.AnonBurstThrottle",
        "core.api.throttling.UserBurstThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1/min",
        "user": "1000/min",
    },
}


@override_settings(REST_FRAMEWORK=THROTTLE_SETTINGS)
def test_throttle(api_client):
    first = api_client.get(reverse("schema"))
    second = api_client.get(reverse("schema"))

    assert first.status_code == status.HTTP_200_OK
    assert second.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "detail" in second.data
