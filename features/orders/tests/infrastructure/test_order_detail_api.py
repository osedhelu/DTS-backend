from decimal import Decimal
from pathlib import Path

import pytest
from django.test.utils import override_settings
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, CustomerProfile, DriverProfile
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
        "TEST": {"NAME": "test_dts_order_detail_api"},
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
def test_assigned_driver_can_get_order_detail(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.orders.infrastructure.models import Order as OrderModel
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_order_detail",
            email="merchant_order_detail@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_order_detail",
            email="customer_order_detail@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        CustomerProfile.objects.create(user=customer, phone="+573001234567")
        driver = CustomUser.objects.create_user(
            username="driver_order_detail",
            email="driver_order_detail@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
        )
        DriverProfile.objects.create(user=driver, phone="+573009998877")

        store = Store(
            owner=merchant,
            name="Tienda Detalle",
            status=StoreStatus.OPEN,
            address="Calle 100 # 10-20",
        )
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Producto Detalle",
            price=Decimal("100.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        order = OrderModel.objects.create(
            customer=customer,
            store=store,
            driver=driver,
            status=OrderStatus.DRIVER_ASSIGNED,
            total=Decimal("100.00"),
        )
        order.items.create(
            product=product,
            product_name=product.name,
            unit_price=product.price,
            quantity=1,
        )

        _auth(api_client, driver)
        response = api_client.get(f"/api/v1/orders/{order.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == order.id
        assert response.data["store_name"] == "Tienda Detalle"
        assert response.data["store_latitude"] == pytest.approx(4.7110)
        assert response.data["store_longitude"] == pytest.approx(-74.0721)
        assert response.data["store_address"] == "Calle 100 # 10-20"
        assert response.data["customer_phone"] == "+573001234567"
        assert response.data["delivery_address"] == "Calle 100 # 10-20"
        assert response.data["delivery_latitude"] == pytest.approx(4.7110)
        assert response.data["delivery_longitude"] == pytest.approx(-74.0721)
        assert response.data["driver_earning"] == "10.00"


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_customer_can_get_order_detail_with_driver(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.orders.infrastructure.models import Order as OrderModel
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_customer_detail",
            email="merchant_customer_detail@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_detail_view",
            email="customer_detail_view@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        CustomerProfile.objects.create(user=customer, phone="+573001234567")
        driver = CustomUser.objects.create_user(
            username="driver_customer_detail",
            email="driver_customer_detail@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
        )
        DriverProfile.objects.create(
            user=driver,
            phone="+573009998877",
            full_name="Carlos Conductor",
        )

        store = Store(
            owner=merchant,
            name="Tienda Cliente",
            status=StoreStatus.OPEN,
            address="Calle comercio 1",
        )
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Producto Cliente",
            price=Decimal("80.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        order = OrderModel.objects.create(
            customer=customer,
            store=store,
            driver=driver,
            status=OrderStatus.DRIVER_ASSIGNED,
            total=Decimal("80.00"),
            service_address="Calle 50 # 10-20",
            customer_notes="Dejar en portería",
            service_latitude=4.65,
            service_longitude=-74.08,
        )
        order.items.create(
            product=product,
            product_name=product.name,
            unit_price=product.price,
            quantity=1,
        )

        _auth(api_client, customer)
        response = api_client.get(f"/api/v1/orders/{order.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["delivery_address"] == "Calle 50 # 10-20"
        assert response.data["delivery_latitude"] == pytest.approx(4.65)
        assert response.data["delivery_longitude"] == pytest.approx(-74.08)
        assert response.data["customer_notes"] == "Dejar en portería"
        assert response.data["driver_name"] == "Carlos Conductor"
        assert response.data["driver_phone"] == "+573009998877"
        assert "driver_earning" not in response.data


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_unauthorized_user_cannot_get_order_detail(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.orders.infrastructure.models import Order as OrderModel
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_order_detail_forbidden",
            email="merchant_order_detail_forbidden@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_order_detail_forbidden",
            email="customer_order_detail_forbidden@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        other_driver = CustomUser.objects.create_user(
            username="other_driver_order_detail",
            email="other_driver_order_detail@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
        )
        DriverProfile.objects.create(user=other_driver, phone="+573001111111")

        store = Store(
            owner=merchant,
            name="Tienda Prohibida",
            status=StoreStatus.OPEN,
        )
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Producto Prohibido",
            price=Decimal("50.00"),
            stock=5,
            product_type=ProductType.PHYSICAL,
        )

        assigned_driver = CustomUser.objects.create_user(
            username="assigned_driver_order_detail",
            email="assigned_driver_order_detail@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
        )
        DriverProfile.objects.create(user=assigned_driver, phone="+573002222222")

        order = OrderModel.objects.create(
            customer=customer,
            store=store,
            driver=assigned_driver,
            status=OrderStatus.DRIVER_ASSIGNED,
            total=Decimal("50.00"),
        )
        order.items.create(
            product=product,
            product_name=product.name,
            unit_price=product.price,
            quantity=1,
        )

        _auth(api_client, other_driver)
        response = api_client.get(f"/api/v1/orders/{order.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN
