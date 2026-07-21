from decimal import Decimal
from pathlib import Path

import pytest
from django.test.utils import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, DriverProfile
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
        "TEST": {"NAME": "test_dts_driver_earnings_api"},
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
def test_driver_earnings_today(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.orders.infrastructure.models import Order as OrderModel
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_driver_earnings",
            email="merchant_driver_earnings@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_driver_earnings",
            email="customer_driver_earnings@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        driver = CustomUser.objects.create_user(
            username="driver_earnings",
            email="driver_earnings@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
        )
        DriverProfile.objects.create(user=driver, phone="+573003333333")

        store = Store(
            owner=merchant,
            name="Tienda Earnings",
            status=StoreStatus.OPEN,
        )
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Producto Earnings",
            price=Decimal("100.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        order = OrderModel.objects.create(
            customer=customer,
            store=store,
            driver=driver,
            status=OrderStatus.DELIVERED,
            total=Decimal("100.00"),
        )
        order.items.create(
            product=product,
            product_name=product.name,
            unit_price=product.price,
            quantity=1,
        )
        OrderModel.objects.filter(pk=order.pk).update(updated_at=timezone.now())

        _auth(api_client, driver)
        response = api_client.get("/api/v1/accounts/driver/earnings/?period=today")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["period"] == "today"
        assert response.data["delivery_count"] == 1
        assert response.data["total_earnings"] == "10.00"
        assert response.data["currency"] == "COP"
        assert len(response.data["breakdown"]) == 1
        assert response.data["breakdown"][0]["order_id"] == order.id
        assert response.data["breakdown"][0]["order_total"] == "100.00"
        assert response.data["breakdown"][0]["earning"] == "10.00"


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_driver_earnings_invalid_period(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        driver = CustomUser.objects.create_user(
            username="driver_earnings_invalid",
            email="driver_earnings_invalid@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
        )
        DriverProfile.objects.create(user=driver, phone="+573004444444")

        _auth(api_client, driver)
        response = api_client.get("/api/v1/accounts/driver/earnings/?period=year")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_customer_cannot_access_driver_earnings(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        customer = CustomUser.objects.create_user(
            username="customer_earnings_forbidden",
            email="customer_earnings_forbidden@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )

        _auth(api_client, customer)
        response = api_client.get("/api/v1/accounts/driver/earnings/")

        assert response.status_code == status.HTTP_403_FORBIDDEN
