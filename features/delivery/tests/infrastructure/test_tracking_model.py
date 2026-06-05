from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from django.test.utils import override_settings

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
        "TEST": {"NAME": "test_dts_delivery"},
    }
}


def _geos_available() -> bool:
    try:
        from django.contrib.gis.geos import Point

        Point(0, 0, srid=4326)
        return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_save_tracking_points():
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.delivery.infrastructure.models import DeliveryTracking, TrackingPoint
        from features.orders.infrastructure.models import Order
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_tracking",
            email="merchant_tracking@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_tracking",
            email="customer_tracking@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )

        store = Store(
            owner=merchant,
            name="Restaurante Central",
            status=StoreStatus.OPEN,
        )
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Hamburguesa",
            price=Decimal("15990.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        order = Order.objects.create(
            customer=customer,
            store=store,
            status=OrderStatus.ON_THE_WAY,
            total=product.price,
        )

        tracking = DeliveryTracking.objects.create(order=order)

        points_data = [
            (4.7110, -74.0721, 1, datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc)),
            (4.7120, -74.0710, 2, datetime(2026, 6, 4, 14, 0, 10, tzinfo=timezone.utc)),
            (4.7130, -74.0700, 3, datetime(2026, 6, 4, 14, 0, 20, tzinfo=timezone.utc)),
        ]

        for latitude, longitude, sequence, recorded_at in points_data:
            point = TrackingPoint(
                tracking=tracking,
                sequence=sequence,
                recorded_at=recorded_at,
            )
            point.set_location(GeoLocation(latitude=latitude, longitude=longitude))
            point.save()

        saved = DeliveryTracking.objects.prefetch_related("points").get(pk=tracking.pk)
        saved_points = list(saved.points.all())

        assert len(saved_points) == 3
        assert [point.sequence for point in saved_points] == [1, 2, 3]
        assert saved_points[0].latitude == pytest.approx(4.7110)
        assert saved_points[0].longitude == pytest.approx(-74.0721)
        assert saved_points[2].latitude == pytest.approx(4.7130)
        assert saved_points[2].longitude == pytest.approx(-74.0700)
        assert saved.order_id == order.id
