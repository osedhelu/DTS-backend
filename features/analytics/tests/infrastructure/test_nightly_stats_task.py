from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from django.test.utils import override_settings
from django.utils import timezone

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.orders.domain.value_objects import OrderStatus
from features.products.domain.entities import ProductType
from features.stores.domain.entities import StoreStatus
from features.stores.domain.value_objects import GeoLocation

BACKEND_DIR = Path(__file__).resolve().parents[4]
BOGOTA = ZoneInfo("America/Bogota")

POSTGIS_DATABASE = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "dts_delivery",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {"NAME": "test_dts_nightly_stats"},
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
def test_nightly_stats_task():
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        TIME_ZONE="America/Bogota",
    ):
        from features.analytics.infrastructure.models import DailySalesReport, DriverCommission
        from features.analytics.infrastructure.repositories import DjangoDailyReportRepository
        from features.analytics.infrastructure.tasks import calculate_daily_stats
        from features.orders.infrastructure.models import Order
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        report_date = date(2026, 6, 4)
        completed_at = timezone.make_aware(
            datetime(2026, 6, 4, 23, 30),
            timezone=BOGOTA,
        )

        merchant = CustomUser.objects.create_user(
            username="merchant_nightly_stats",
            email="merchant_nightly_stats@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_nightly_stats",
            email="customer_nightly_stats@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        driver = CustomUser.objects.create_user(
            username="driver_nightly_stats",
            email="driver_nightly_stats@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
        )

        store = Store(owner=merchant, name="Nightly Stats Store", status=StoreStatus.OPEN)
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        product = Product.objects.create(
            store=store,
            name="Nightly Stats Product",
            price=Decimal("25000.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        order = Order.objects.create(
            customer=customer,
            store=store,
            driver=driver,
            status=OrderStatus.DELIVERED,
            total=product.price,
        )
        Order.objects.filter(pk=order.pk).update(
            updated_at=completed_at,
            total=product.price,
        )

        stale_order = Order.objects.create(
            customer=customer,
            store=store,
            driver=driver,
            status=OrderStatus.DELIVERED,
            total=Decimal("10000.00"),
        )
        Order.objects.filter(pk=stale_order.pk).update(
            updated_at=completed_at - timedelta(days=1),
            total=Decimal("10000.00"),
        )

        result = calculate_daily_stats(report_date.isoformat())

        assert result == f"saved:{report_date.isoformat()}:1:25000.00"
        assert DailySalesReport.objects.filter(report_date=report_date).count() == 1
        assert DriverCommission.objects.filter(report_date=report_date).count() == 1

        loaded = DjangoDailyReportRepository().get_by_date(report_date)
        assert loaded is not None
        assert loaded.total_orders == 1
        assert loaded.total_revenue == Decimal("25000.00")
        assert loaded.driver_commissions[0].commission_amount == Decimal("2500.00")
