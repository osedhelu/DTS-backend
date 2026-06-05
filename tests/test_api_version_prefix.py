from django.urls import reverse


API_V1_PREFIX = "/api/v1/"

NAMED_API_ROUTES: tuple[tuple[str, tuple], ...] = (
    ("schema", ()),
    ("swagger", ()),
    ("accounts-register", ()),
    ("accounts-login", ()),
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


def test_api_version_prefix():
    for route_name, args in NAMED_API_ROUTES:
        url = reverse(route_name, args=args)
        assert url.startswith(API_V1_PREFIX), (
            f"La ruta '{route_name}' debe estar bajo '{API_V1_PREFIX}', obtuvo: {url}"
        )


def test_api_v1_root_is_not_empty():
    url = reverse("schema")
    assert url == f"{API_V1_PREFIX}schema/"
