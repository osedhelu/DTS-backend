from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
from celery.exceptions import Retry
from django.test.utils import override_settings

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
        "TEST": {"NAME": "test_dts_assign_driver_task"},
    }
}


def _geos_available() -> bool:
    try:
        from django.contrib.gis.geos import Point

        Point(0, 0, srid=4326)
        return True
    except Exception:
        return False


def _create_driver(username: str, email: str, location: GeoLocation) -> CustomUser:
    driver = CustomUser.objects.create_user(
        username=username,
        email=email,
        password="securepass123",
        role=UserRole.DRIVER,
    )
    profile = DriverProfile.objects.create(
        user=driver,
        phone="3001234567",
        is_online=True,
    )
    profile.set_last_location(location)
    profile.save(update_fields=["last_latitude", "last_longitude", "updated_at"])
    return driver


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_task_assigns_nearest():
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
    ):
        from features.delivery.infrastructure.tasks import assign_driver_task
        from features.orders.infrastructure.models import Order
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_assign_task",
            email="merchant_assign_task@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_assign_task",
            email="customer_assign_task@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )

        pickup = GeoLocation(latitude=4.7110, longitude=-74.0721)
        store = Store(owner=merchant, name="Assign Task Store", status=StoreStatus.OPEN)
        store.set_location(pickup)
        store.save()

        product = Product.objects.create(
            store=store,
            name="Assign Task Product",
            price=Decimal("10000.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        far_driver = _create_driver(
            "driver_far",
            "driver_far@test.com",
            GeoLocation(latitude=4.6500, longitude=-74.1000),
        )
        nearest_driver = _create_driver(
            "driver_near",
            "driver_near@test.com",
            GeoLocation(latitude=4.7120, longitude=-74.0710),
        )
        _create_driver(
            "driver_farther",
            "driver_farther@test.com",
            GeoLocation(latitude=4.8000, longitude=-74.0000),
        )

        order = Order.objects.create(
            customer=customer,
            store=store,
            status=OrderStatus.READY_FOR_PICKUP,
            total=product.price,
        )

        result = assign_driver_task(order.id)

        order.refresh_from_db()
        assert result == f"assigned:{order.id}:{nearest_driver.id}"
        assert order.driver_id == nearest_driver.id
        assert order.driver_id != far_driver.id


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_task_retries():
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
    ):
        from features.delivery.infrastructure.tasks import assign_driver_task
        from features.orders.infrastructure.models import Order
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_retry_task",
            email="merchant_retry_task@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_retry_task",
            email="customer_retry_task@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )

        store = Store(owner=merchant, name="Retry Task Store", status=StoreStatus.OPEN)
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Retry Task Product",
            price=Decimal("10000.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        order = Order.objects.create(
            customer=customer,
            store=store,
            status=OrderStatus.READY_FOR_PICKUP,
            total=product.price,
        )

        with patch.object(assign_driver_task, "retry", side_effect=Retry()) as mock_retry:
            with pytest.raises(Retry):
                assign_driver_task.run(order.id)

        mock_retry.assert_called_once()
        order.refresh_from_db()
        assert order.driver_id is None
