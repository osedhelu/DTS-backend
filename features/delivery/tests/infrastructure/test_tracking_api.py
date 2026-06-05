from datetime import datetime, timezone
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
        "TEST": {"NAME": "test_dts_tracking_api"},
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
def test_driver_posts_location(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.orders.infrastructure.models import Order
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_tracking_api",
            email="merchant_tracking_api@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_tracking_api",
            email="customer_tracking_api@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        driver = CustomUser.objects.create_user(
            username="driver_tracking_api",
            email="driver_tracking_api@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
        )

        store = Store(
            owner=merchant,
            name="Restaurante Tracking",
            status=StoreStatus.OPEN,
        )
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Hamburguesa Tracking",
            price=Decimal("15990.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        order = Order.objects.create(
            customer=customer,
            store=store,
            driver=driver,
            status=OrderStatus.ON_THE_WAY,
            total=product.price,
        )

        _auth(api_client, driver)
        recorded_at = datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc)
        response = api_client.post(
            f"/api/v1/orders/{order.id}/tracking/",
            {
                "latitude": 4.7110,
                "longitude": -74.0721,
                "recorded_at": recorded_at.isoformat(),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["order_id"] == order.id
        assert response.data["point_count"] == 1
        assert len(response.data["points"]) == 1
        assert response.data["points"][0]["sequence"] == 1
        assert response.data["points"][0]["latitude"] == pytest.approx(4.7110)
        assert response.data["points"][0]["longitude"] == pytest.approx(-74.0721)


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_customer_reads_tracking(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.delivery.infrastructure.models import DeliveryTracking, TrackingPoint
        from features.orders.infrastructure.models import Order
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_tracking_read",
            email="merchant_tracking_read@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_tracking_read",
            email="customer_tracking_read@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        driver = CustomUser.objects.create_user(
            username="driver_tracking_read",
            email="driver_tracking_read@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
        )
        other_customer = CustomUser.objects.create_user(
            username="other_customer_tracking",
            email="other_customer_tracking@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )

        store = Store(
            owner=merchant,
            name="Restaurante Lectura",
            status=StoreStatus.OPEN,
        )
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Hamburguesa Lectura",
            price=Decimal("15990.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        order = Order.objects.create(
            customer=customer,
            store=store,
            driver=driver,
            status=OrderStatus.ON_THE_WAY,
            total=product.price,
        )

        tracking = DeliveryTracking.objects.create(order=order)
        points_data = [
            (4.7110, -74.0721, 1, datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc)),
            (4.7120, -74.0710, 2, datetime(2026, 6, 4, 14, 0, 10, tzinfo=timezone.utc)),
        ]
        for latitude, longitude, sequence, recorded_at in points_data:
            point = TrackingPoint(
                tracking=tracking,
                sequence=sequence,
                recorded_at=recorded_at,
            )
            point.set_location(GeoLocation(latitude=latitude, longitude=longitude))
            point.save()

        _auth(api_client, customer)
        response = api_client.get(f"/api/v1/orders/{order.id}/tracking/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["order_id"] == order.id
        assert response.data["point_count"] == 2
        assert [point["sequence"] for point in response.data["points"]] == [1, 2]
        assert response.data["points"][0]["latitude"] == pytest.approx(4.7110)
        assert response.data["points"][1]["latitude"] == pytest.approx(4.7120)

        _auth(api_client, other_customer)
        forbidden = api_client.get(f"/api/v1/orders/{order.id}/tracking/")
        assert forbidden.status_code == status.HTTP_403_FORBIDDEN
