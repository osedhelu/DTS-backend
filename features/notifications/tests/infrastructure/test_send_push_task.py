from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.test.utils import override_settings

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, DeviceToken
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
        "TEST": {"NAME": "test_dts_send_push_task"},
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
def test_send_push_task_calls_fcm():
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        FCM_CREDENTIALS_PATH="/tmp/fake-service-account.json",
    ):
        from features.notifications.infrastructure.tasks import send_push_task
        from features.orders.infrastructure.models import Order
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_send_push",
            email="merchant_send_push@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_send_push",
            email="customer_send_push@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        DeviceToken.objects.create(
            user=customer,
            token="customer-fcm-token",
            platform="android",
            is_active=True,
        )

        store = Store(owner=merchant, name="Send Push Store", status=StoreStatus.OPEN)
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Send Push Product",
            price=Decimal("10000.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        order = Order.objects.create(
            customer=customer,
            store=store,
            status=OrderStatus.ACCEPTED_BY_MERCHANT,
            total=product.price,
        )

        mock_fcm = MagicMock()
        mock_fcm.send.return_value = "projects/test/messages/push-1"

        with patch(
            "features.notifications.infrastructure.tasks.get_fcm_client",
            return_value=mock_fcm,
        ):
            result = send_push_task(order.id, OrderStatus.ACCEPTED_BY_MERCHANT)

        assert result == f"sent:{order.id}:1"
        mock_fcm.send.assert_called_once_with(
            token="customer-fcm-token",
            title="Pedido aceptado",
            body="Tu pedido fue aceptado",
            data={
                "notification_type": "order_accepted",
                "order_id": str(order.id),
                "order_status": "accepted_by_merchant",
            },
        )
