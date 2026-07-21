from decimal import Decimal
from pathlib import Path

import pytest
from django.test.utils import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.marketing.infrastructure.models import CouponModel
from features.orders.domain.value_objects import OrderStatus
from features.payments.infrastructure.models import StorePaymentMethod
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
        "TEST": {"NAME": "test_dts_service_order_pay"},
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
def test_service_order_with_payment_and_coupon(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_service_pay",
            email="merchant_service_pay@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_service_pay",
            email="customer_service_pay@test.com",
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
            name="Lavado express",
            price=Decimal("45000.00"),
            stock=0,
            product_type=ProductType.SERVICE,
            duration_minutes=60,
        )

        StorePaymentMethod.objects.create(
            store=store,
            name="Efectivo",
            method_type="cash",
            is_active=True,
        )
        cash_method = StorePaymentMethod.objects.get(store=store, method_type="cash")

        CouponModel.objects.create(
            code="LAVADO10",
            discount_type="fixed",
            discount_value=Decimal("5000.00"),
            min_order_total=Decimal("10000.00"),
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_until=timezone.now() + timezone.timedelta(days=30),
            is_active=True,
        )

        _auth(api_client, customer)
        response = api_client.post(
            "/api/v1/orders/service/",
            {
                "store_id": store.id,
                "items": [{"product_id": service.id, "quantity": 1}],
                "service_address": "Carrera 7 # 45-10",
                "customer_notes": "Detalles del servicio:\nkg: 5",
                "payment_method_id": cash_method.id,
                "coupon_code": "LAVADO10",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == OrderStatus.CREATED
        assert response.data["order_type"] == "service"
        assert response.data["payment_status"] == "cash_on_delivery"
        assert response.data["discount_amount"] == "5000.00"
        assert response.data["total"] == "40000.00"
        assert response.data["customer_notes"] == "Detalles del servicio:\nkg: 5"
