from django.test.utils import override_settings
from django.urls import path
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.throttling import AnonBurstThrottle


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


class _ThrottleProbeView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonBurstThrottle]

    def get(self, request):
        return Response({"ok": True}, status=status.HTTP_200_OK)


urlpatterns = [
    path("test/throttle-probe/", _ThrottleProbeView.as_view(), name="throttle-probe"),
]


@override_settings(ROOT_URLCONF="tests.test_throttle")
def test_throttle(api_client):
    cache.clear()
    original_rates = dict(AnonBurstThrottle.THROTTLE_RATES)
    AnonBurstThrottle.THROTTLE_RATES = {"anon": "1/min"}
    try:
        first = api_client.get("/test/throttle-probe/")
        second = api_client.get("/test/throttle-probe/")

        assert first.status_code == status.HTTP_200_OK
        assert second.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "detail" in second.data
    finally:
        AnonBurstThrottle.THROTTLE_RATES = original_rates
