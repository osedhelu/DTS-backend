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
        "TEST": {"NAME": "test_dts_sandbox_pay"},
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
def test_sandbox_pay_marks_order_paid(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
        PAYMENT_SANDBOX_ENABLED=True,
    ):
        from features.orders.infrastructure.models import Order
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_sandbox",
            email="merchant_sandbox@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_sandbox",
            email="customer_sandbox@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )

        store = Store(
            owner=merchant,
            name="Tienda Sandbox",
            status=StoreStatus.OPEN,
        )
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Producto Sandbox",
            price=Decimal("25000.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        _auth(api_client, customer)
        create_response = api_client.post(
            "/api/v1/orders/",
            {
                "store_id": store.id,
                "items": [{"product_id": product.id, "quantity": 1}],
                "delivery_address": "Calle 10 # 20-30",
            },
            format="json",
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        order_id = create_response.data["id"]
        assert create_response.data["payment_status"] == "pending"

        pay_response = api_client.post(
            f"/api/v1/orders/{order_id}/sandbox-pay/",
            {"card_last4": "4242"},
            format="json",
        )
        assert pay_response.status_code == status.HTTP_200_OK
        assert pay_response.data["payment_status"] == "paid"
        assert pay_response.data["total_paid"] == "25000.00"
        assert pay_response.data["payment_method_label"] == "Sandbox DTS"
        assert "platform_commission" in pay_response.data
        assert "merchant_net" in pay_response.data

        order = Order.objects.get(pk=order_id)
        assert order.payment_status == "paid"
        assert order.paid_at is not None
        assert order.payment_reference.startswith("sandbox:")


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_sandbox_pay_disabled_returns_403(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
        PAYMENT_SANDBOX_ENABLED=False,
    ):
        customer = CustomUser.objects.create_user(
            username="customer_sandbox_off",
            email="customer_sandbox_off@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        _auth(api_client, customer)
        response = api_client.post(
            "/api/v1/orders/999/sandbox-pay/",
            {"card_last4": "4242"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
