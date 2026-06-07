from decimal import Decimal
from pathlib import Path

import pytest
from django.test.utils import override_settings
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.orders.domain.value_objects import OrderStatus, OrderType
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
        "TEST": {"NAME": "test_dts_service_orders_api"},
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
def test_create_service_order_api(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_service_api",
            email="merchant_service_api@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_service_api",
            email="customer_service_api@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )

        store = Store(
            owner=merchant,
            name="Limpieza Express",
            status=StoreStatus.OPEN,
        )
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        service = Product.objects.create(
            store=store,
            name="Limpieza profunda",
            price=Decimal("85000.00"),
            product_type=ProductType.SERVICE,
            requires_on_site_visit=True,
            duration_minutes=180,
        )

        _auth(api_client, customer)
        response = api_client.post(
            "/api/v1/orders/service/",
            {
                "store_id": store.id,
                "items": [{"product_id": service.id, "quantity": 1}],
                "service_address": "Calle 100 #15-20, Bogotá",
                "customer_notes": "Timbre roto, llamar al llegar",
                "latitude": 4.7110,
                "longitude": -74.0721,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["order_type"] == OrderType.SERVICE
        assert response.data["status"] == OrderStatus.CREATED
        assert response.data["service_address"] == "Calle 100 #15-20, Bogotá"
        assert response.data["customer_notes"] == "Timbre roto, llamar al llegar"
        assert response.data["duration_minutes"] == 180
        assert response.data["total"] == "85000.00"


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_service_order_requires_address(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_no_address",
            email="merchant_no_address@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_no_address",
            email="customer_no_address@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )

        store = Store(
            owner=merchant,
            name="Servicios Hogar",
            status=StoreStatus.OPEN,
        )
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        service = Product.objects.create(
            store=store,
            name="Plomería básica",
            price=Decimal("60000.00"),
            product_type=ProductType.SERVICE,
            requires_on_site_visit=True,
        )

        _auth(api_client, customer)
        response = api_client.post(
            "/api/v1/orders/service/",
            {
                "store_id": store.id,
                "items": [{"product_id": service.id, "quantity": 1}],
                "service_address": "   ",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "dirección" in str(response.data).lower()
