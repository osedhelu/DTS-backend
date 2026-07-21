from decimal import Decimal
from pathlib import Path

import pytest
from django.test.utils import override_settings
from rest_framework_simplejwt.tokens import RefreshToken

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import (
    CustomUser,
    CustomerProfile,
    DriverProfile,
)
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
        "TEST": {"NAME": "test_dts_merchant_order_enrichment"},
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
def test_merchant_order_list_includes_customer_and_driver(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.orders.infrastructure.models import Order, OrderItem
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_enrich",
            email="merchant_enrich@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_enrich",
            email="customer_enrich@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        CustomerProfile.objects.create(
            user=customer,
            full_name="Ana Cliente",
            phone="+573001112233",
        )
        driver = CustomUser.objects.create_user(
            username="driver_enrich",
            email="driver_enrich@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
        )
        DriverProfile.objects.create(
            user=driver,
            full_name="Carlos Conductor",
            phone="+573009998877",
        )

        store = Store(owner=merchant, name="Tienda Enrich", status=StoreStatus.OPEN)
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Pizza Enrich",
            price=Decimal("20.00"),
            product_type=ProductType.PHYSICAL,
            is_active=True,
        )

        order = Order.objects.create(
            customer=customer,
            store=store,
            driver=driver,
            status=OrderStatus.DRIVER_ASSIGNED,
            order_type=OrderType.DELIVERY,
            service_address="Calle 100 # 10-20",
            customer_notes="Timbre rojo",
            service_latitude=4.7200,
            service_longitude=-74.0500,
            total=Decimal("20.00"),
            payment_status="cash_on_delivery",
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            unit_price=product.price,
            quantity=1,
        )

        _auth(api_client, merchant)
        response = api_client.get("/api/v1/orders/")

        assert response.status_code == 200
        results = response.data["results"]
        assert len(results) == 1
        row = results[0]
        assert row["customer_name"] == "Ana Cliente"
        assert row["customer_phone"] == "+573001112233"
        assert row["driver_name"] == "Carlos Conductor"
        assert row["driver_phone"] == "+573009998877"
        assert row["delivery_address"] == "Calle 100 # 10-20"
        assert row["service_address"] == "Calle 100 # 10-20"
        assert row["customer_notes"] == "Timbre rojo"
        assert row["created_at"] is not None

        detail = api_client.get(f"/api/v1/orders/{order.id}/")
        assert detail.status_code == 200
        assert detail.data["customer_name"] == "Ana Cliente"
        assert detail.data["driver_name"] == "Carlos Conductor"
        assert detail.data["delivery_address"] == "Calle 100 # 10-20"
