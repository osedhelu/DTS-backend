from datetime import datetime, time, timedelta
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
from features.orders.domain.value_objects import OrderStatus
from tests.gis_helpers import POSTGIS_DATABASE, create_test_store, postgis_tests_available

COMPLETED_ORDER_STATUSES = (
    OrderStatus.DELIVERED.value,
    OrderStatus.COMPLETED.value,
)

BACKEND_DIR = Path(__file__).resolve().parents[4]


def _auth(api_client, user):
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_merchant_dashboard_api(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.orders.domain.value_objects import OrderStatus, OrderType
        from features.orders.infrastructure.models import Order, OrderItem
        from features.products.domain.entities import ProductType
        from features.products.infrastructure.models import Product

        merchant = CustomUser.objects.create_user(
            username="merchant_dashboard",
            email="merchant_dashboard@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        other_merchant = CustomUser.objects.create_user(
            username="other_merchant",
            email="other_merchant@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_dashboard",
            email="customer_dashboard@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )

        store = create_test_store(merchant, name="Dashboard Store")
        product = Product.objects.create(
            store=store,
            name="Hamburguesa premium",
            price=Decimal("25000.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
            is_active=True,
        )
        Product.objects.create(
            store=store,
            name="Inactivo",
            price=Decimal("10000.00"),
            stock=0,
            product_type=ProductType.PHYSICAL,
            is_active=False,
        )

        today = timezone.now()
        today_date = timezone.localdate()
        week_start_date = today_date - timedelta(days=today_date.weekday())
        older_in_week = today - timedelta(days=1)
        if older_in_week.date() < week_start_date:
            older_in_week = timezone.make_aware(
                datetime.combine(week_start_date, time(10, 0)),
                timezone.get_current_timezone(),
            )

        order = Order.objects.create(
            customer=customer,
            store=store,
            status=OrderStatus.DELIVERED.value,
            order_type=OrderType.DELIVERY.value,
            total=Decimal("50000.00"),
        )
        Order.objects.filter(pk=order.pk).update(updated_at=today)
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            unit_price=Decimal("25000.00"),
            quantity=2,
        )

        old_order = Order.objects.create(
            customer=customer,
            store=store,
            status=OrderStatus.COMPLETED.value,
            order_type=OrderType.SERVICE.value,
            total=Decimal("80000.00"),
        )
        Order.objects.filter(pk=old_order.pk).update(updated_at=older_in_week)

        orders_today_expected = Order.objects.filter(
            store=store,
            status__in=COMPLETED_ORDER_STATUSES,
            updated_at__date=today_date,
        ).count()
        orders_this_week_expected = Order.objects.filter(
            store=store,
            status__in=COMPLETED_ORDER_STATUSES,
            updated_at__date__gte=week_start_date,
            updated_at__date__lte=today_date,
        ).count()

        _auth(api_client, merchant)
        response = api_client.get(
            f"/api/v1/stores/{store.pk}/merchant-dashboard/?days=30",
        )

        assert response.status_code == status.HTTP_200_OK
        payload = response.json()
        assert payload["store_id"] == store.pk
        assert payload["order_count"] == 2
        assert payload["total_sales"] == "130000.00"
        assert payload["active_products"] == 1
        assert payload["orders_today"] == orders_today_expected
        assert payload["orders_this_week"] == orders_this_week_expected
        assert payload["platform_commission"] == "19500.00"
        assert payload["net_earnings"] == "110500.00"
        assert len(payload["sales_series"]) == 30
        assert payload["top_products"][0]["product_name"] == "Hamburguesa premium"

        _auth(api_client, other_merchant)
        forbidden = api_client.get(
            f"/api/v1/stores/{store.pk}/merchant-dashboard/",
        )
        assert forbidden.status_code == status.HTTP_403_FORBIDDEN
