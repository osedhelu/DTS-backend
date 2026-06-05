from decimal import Decimal
from pathlib import Path

import pytest
from django.test.utils import override_settings
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.orders.domain.value_objects import OrderStatus
from features.products.domain.entities import ProductType
from features.stores.domain.entities import StoreStatus
from features.stores.domain.value_objects import GeoLocation

BACKEND_DIR = Path(__file__).resolve().parents[4]

POSTGIS_DATABASE = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "dts_delivery",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {"NAME": "test_dts_orders_api"},
    }
}


def _geos_available() -> bool:
    try:
        from django.contrib.gis.geos import Point

        Point(0, 0, srid=4326)
        return True
    except Exception:
        return False


def _auth(api_client, user):
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_order_api_flow(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_orders_api",
            email="merchant_orders_api@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_orders_api",
            email="customer_orders_api@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )

        store = Store(
            owner=merchant,
            name="Restaurante API",
            status=StoreStatus.OPEN,
        )
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Hamburguesa API",
            price=Decimal("15990.00"),
            stock=20,
            product_type=ProductType.PHYSICAL,
        )

        _auth(api_client, customer)
        create_response = api_client.post(
            "/api/v1/orders/",
            {
                "store_id": store.id,
                "items": [{"product_id": product.id, "quantity": 2}],
            },
            format="json",
        )

        assert create_response.status_code == status.HTTP_201_CREATED
        assert create_response.data["status"] == OrderStatus.CREATED
        assert create_response.data["total"] == "31980.00"
        order_id = create_response.data["id"]

        customer_list = api_client.get("/api/v1/orders/")
        assert customer_list.status_code == status.HTTP_200_OK
        assert len(customer_list.data) == 1
        assert customer_list.data[0]["id"] == order_id

        _auth(api_client, merchant)
        merchant_list = api_client.get("/api/v1/orders/")
        assert merchant_list.status_code == status.HTTP_200_OK
        assert len(merchant_list.data) == 1
        assert merchant_list.data[0]["status"] == OrderStatus.CREATED

        accept_response = api_client.patch(
            f"/api/v1/orders/{order_id}/",
            {"status": OrderStatus.ACCEPTED_BY_MERCHANT},
            format="json",
        )
        assert accept_response.status_code == status.HTTP_200_OK
        assert accept_response.data["status"] == OrderStatus.ACCEPTED_BY_MERCHANT

        _auth(api_client, customer)
        customer_accept = api_client.patch(
            f"/api/v1/orders/{order_id}/",
            {"status": OrderStatus.ACCEPTED_BY_MERCHANT},
            format="json",
        )
        assert customer_accept.status_code == status.HTTP_403_FORBIDDEN
