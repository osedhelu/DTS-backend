from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from django.test.utils import override_settings

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.analytics.domain.entities import CompletedOrderSnapshot
from features.analytics.domain.services import DailyReportAggregator
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
        "TEST": {"NAME": "test_dts_analytics_reports"},
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
def test_report_persistence():
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.analytics.infrastructure.models import DailySalesReport, DriverCommission
        from features.analytics.infrastructure.repositories import DjangoDailyReportRepository
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_report_persist",
            email="merchant_report_persist@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        driver = CustomUser.objects.create_user(
            username="driver_report_persist",
            email="driver_report_persist@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
        )

        store = Store(owner=merchant, name="Report Persist Store", status=StoreStatus.OPEN)
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        report_date = date(2026, 6, 5)
        report = DailyReportAggregator.aggregate(
            report_date,
            [
                CompletedOrderSnapshot(
                    order_id=1,
                    store_id=store.id,
                    driver_id=driver.id,
                    total=Decimal("40000.00"),
                    completed_on=report_date,
                ),
                CompletedOrderSnapshot(
                    order_id=2,
                    store_id=store.id,
                    driver_id=driver.id,
                    total=Decimal("10000.00"),
                    completed_on=report_date,
                ),
            ],
        )

        repository = DjangoDailyReportRepository()
        repository.save(report)

        assert DailySalesReport.objects.filter(report_date=report_date).count() == 1
        assert DriverCommission.objects.filter(report_date=report_date).count() == 1

        loaded = repository.get_by_date(report_date)

        assert loaded is not None
        assert loaded.report_date == report_date
        assert loaded.total_orders == 2
        assert loaded.total_revenue == Decimal("50000.00")
        assert loaded.store_sales[0].store_id == store.id
        assert loaded.store_sales[0].order_count == 2
        assert loaded.driver_commissions[0].driver_id == driver.id
        assert loaded.driver_commissions[0].delivery_count == 2
        assert loaded.driver_commissions[0].commission_amount == Decimal("5000.00")
