import pytest
from django.urls import reverse

from tests.gis_helpers import postgis_tests_available


API_V1_PREFIX = "/api/v1/"

NAMED_API_ROUTES: tuple[tuple[str, tuple], ...] = (
    ("schema", ()),
    ("swagger", ()),
    ("accounts-register", ()),
    ("accounts-login", ()),
    ("accounts-merchant-register", ()),
    ("accounts-verify-email", ()),
    ("accounts-resend-verification", ()),
    ("accounts-device-token", ()),
    ("accounts-admin-dashboard", ()),
    ("stores-list-create", ()),
    ("stores-detail", (1,)),
    ("store-products-list-create", (1,)),
    ("store-products-detail", (1, 1)),
    ("store-categories-list-create", (1,)),
    ("orders-list-create", ()),
    ("orders-service-create", ()),
    ("orders-detail", (1,)),
    ("order-tracking", (1,)),
)


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido para resolver rutas del API completo",
)
def test_api_version_prefix():
    for route_name, args in NAMED_API_ROUTES:
        url = reverse(route_name, args=args)
        assert url.startswith(API_V1_PREFIX), (
            f"La ruta '{route_name}' debe estar bajo '{API_V1_PREFIX}', obtuvo: {url}"
        )


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido para resolver rutas del API completo",
)
def test_api_v1_root_is_not_empty():
    url = reverse("schema")
    assert url == f"{API_V1_PREFIX}schema/"
