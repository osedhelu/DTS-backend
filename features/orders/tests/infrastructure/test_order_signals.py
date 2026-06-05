from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
from django.dispatch import receiver
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
        "TEST": {"NAME": "test_dts_order_signals"},
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
def test_signal_fires_on_status_change():
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.orders.infrastructure.models import Order
        from features.orders.infrastructure.signals import order_status_changed
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_signal",
            email="merchant_signal@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_signal",
            email="customer_signal@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )

        store = Store(owner=merchant, name="Signal Store", status=StoreStatus.OPEN)
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Signal Product",
            price=Decimal("10000.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        order = Order.objects.create(
            customer=customer,
            store=store,
            status=OrderStatus.CREATED,
            total=product.price,
        )

        captured: list[dict] = []

        @receiver(order_status_changed)
        def _capture_status_change(sender, **kwargs):
            captured.append(kwargs)

        try:
            order.status = OrderStatus.ACCEPTED_BY_MERCHANT
            order.save(update_fields=["status", "updated_at"])
        finally:
            order_status_changed.disconnect(_capture_status_change)

        assert len(captured) == 1
        assert captured[0]["order_id"] == order.id
        assert captured[0]["previous_status"] == OrderStatus.CREATED
        assert captured[0]["current_status"] == OrderStatus.ACCEPTED_BY_MERCHANT


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
@patch("features.delivery.infrastructure.tasks.assign_driver_task.delay")
def test_signal_enqueues_assign_driver(mock_delay):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.orders.infrastructure.models import Order
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_assign_signal",
            email="merchant_assign_signal@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_assign_signal",
            email="customer_assign_signal@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )

        store = Store(owner=merchant, name="Assign Signal Store", status=StoreStatus.OPEN)
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Assign Signal Product",
            price=Decimal("10000.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        order = Order.objects.create(
            customer=customer,
            store=store,
            status=OrderStatus.IN_PREPARATION,
            total=product.price,
        )

        order.status = OrderStatus.READY_FOR_PICKUP
        order.save(update_fields=["status", "updated_at"])

        mock_delay.assert_called_once_with(order.id)

        mock_delay.reset_mock()
        order.status = OrderStatus.SEARCHING_DRIVER
        order.save(update_fields=["status", "updated_at"])

        mock_delay.assert_not_called()


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
@patch("features.notifications.infrastructure.tasks.notify_customer_task.delay")
def test_signal_enqueues_notification(mock_delay):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.orders.infrastructure.models import Order
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_notify_signal",
            email="merchant_notify_signal@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_notify_signal",
            email="customer_notify_signal@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        driver = CustomUser.objects.create_user(
            username="driver_notify_signal",
            email="driver_notify_signal@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
        )

        store = Store(owner=merchant, name="Notify Signal Store", status=StoreStatus.OPEN)
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Notify Signal Product",
            price=Decimal("10000.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        order = Order.objects.create(
            customer=customer,
            store=store,
            driver=driver,
            status=OrderStatus.PICKED_UP,
            total=product.price,
        )

        order.status = OrderStatus.ON_THE_WAY
        order.save(update_fields=["status", "updated_at"])

        mock_delay.assert_called_once_with(order.id)

        mock_delay.reset_mock()
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status", "updated_at"])

        mock_delay.assert_not_called()


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
@patch("features.notifications.infrastructure.tasks.send_push_task.delay")
def test_signal_push_order_accepted(mock_delay):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.orders.infrastructure.models import Order
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_push_signal",
            email="merchant_push_signal@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_push_signal",
            email="customer_push_signal@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )

        store = Store(owner=merchant, name="Push Signal Store", status=StoreStatus.OPEN)
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Push Signal Product",
            price=Decimal("10000.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        order = Order.objects.create(
            customer=customer,
            store=store,
            status=OrderStatus.CREATED,
            total=product.price,
        )

        order.status = OrderStatus.ACCEPTED_BY_MERCHANT
        order.save(update_fields=["status", "updated_at"])

        mock_delay.assert_called_once_with(order.id, OrderStatus.ACCEPTED_BY_MERCHANT)

        mock_delay.reset_mock()
        order.status = OrderStatus.IN_PREPARATION
        order.save(update_fields=["status", "updated_at"])

        mock_delay.assert_not_called()


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
@patch("features.notifications.infrastructure.tasks.notify_drivers_new_order_task.delay")
def test_signal_push_new_order_to_drivers(mock_delay):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.orders.infrastructure.models import Order
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_drivers_push_signal",
            email="merchant_drivers_push_signal@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_drivers_push_signal",
            email="customer_drivers_push_signal@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )

        store = Store(owner=merchant, name="Drivers Push Store", status=StoreStatus.OPEN)
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Drivers Push Product",
            price=Decimal("10000.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        order = Order.objects.create(
            customer=customer,
            store=store,
            status=OrderStatus.IN_PREPARATION,
            total=product.price,
        )

        order.status = OrderStatus.READY_FOR_PICKUP
        order.save(update_fields=["status", "updated_at"])

        mock_delay.assert_called_once_with(order.id)

        mock_delay.reset_mock()
        order.status = OrderStatus.SEARCHING_DRIVER
        order.save(update_fields=["status", "updated_at"])

        mock_delay.assert_not_called()
