from decimal import Decimal
from pathlib import Path

import pytest
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
def test_task_opens_searching_without_assigning():
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

        _create_driver(
            "driver_near",
            "driver_near@test.com",
            GeoLocation(latitude=4.7120, longitude=-74.0710),
        )

        order = Order.objects.create(
            customer=customer,
            store=store,
            status=OrderStatus.READY_FOR_PICKUP,
            total=product.price,
        )

        result = assign_driver_task(order.id)

        order.refresh_from_db()
        assert result == f"searching:{order.id}"
        assert order.driver_id is None
        assert order.status == OrderStatus.SEARCHING_DRIVER


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_accept_offer_first_wins():
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.delivery.application.use_cases.accept_offer import AcceptOfferUseCase
        from features.delivery.domain.exceptions import OfferAlreadyTakenError
        from features.orders.infrastructure.models import Order
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_accept",
            email="merchant_accept@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_accept",
            email="customer_accept@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        store = Store(owner=merchant, name="Accept Store", status=StoreStatus.OPEN)
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()
        product = Product.objects.create(
            store=store,
            name="P",
            price=Decimal("10000.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )
        d1 = _create_driver(
            "d1", "d1@test.com", GeoLocation(latitude=4.7120, longitude=-74.0710)
        )
        d2 = _create_driver(
            "d2", "d2@test.com", GeoLocation(latitude=4.7130, longitude=-74.0700)
        )
        order = Order.objects.create(
            customer=customer,
            store=store,
            status=OrderStatus.SEARCHING_DRIVER,
            total=product.price,
        )

        AcceptOfferUseCase().execute(order.id, d1.id)
        order.refresh_from_db()
        assert order.driver_id == d1.id
        assert order.status == OrderStatus.DRIVER_ASSIGNED

        with pytest.raises(OfferAlreadyTakenError):
            AcceptOfferUseCase().execute(order.id, d2.id)
