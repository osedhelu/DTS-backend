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
        "TEST": {"NAME": "test_dts_orders"},
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
def test_order_persistence():
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.orders.infrastructure.models import Order, OrderItem
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_order",
            email="merchant_order@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_order",
            email="customer_order@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        driver = CustomUser.objects.create_user(
            username="driver_order",
            email="driver_order@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
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
            driver=driver,
            status=OrderStatus.ACCEPTED_BY_MERCHANT,
            total=Decimal("0"),
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            unit_price=product.price,
            quantity=2,
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name="Papas",
            unit_price=Decimal("5900.00"),
            quantity=1,
        )

        order.total = order.compute_total()
        order.save(update_fields=["total", "updated_at"])

        saved = Order.objects.prefetch_related("items").select_related(
            "customer", "store", "driver"
        ).get(pk=order.pk)

        assert saved.customer_id == customer.id
        assert saved.store_id == store.id
        assert saved.driver_id == driver.id
        assert saved.status == OrderStatus.ACCEPTED_BY_MERCHANT
        assert saved.total == Decimal("37880.00")
        assert saved.items.count() == 2
        assert saved.items.first().product_id == product.id
