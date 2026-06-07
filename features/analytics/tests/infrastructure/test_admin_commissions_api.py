from pathlib import Path

import pytest
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser

BACKEND_DIR = Path(__file__).resolve().parents[4]

POSTGIS_DATABASE = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "dts_delivery",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {"NAME": "test_dts_admin_commissions_api"},
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
def test_admin_commissions_list_returns_store_sales_and_driver_commissions():
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.analytics.infrastructure.models import (
            DailySalesReport,
            DriverCommission,
        )
        from tests.gis_helpers import create_test_store

        super_admin = CustomUser.objects.create_user(
            username="superadmin",
            email="super@example.com",
            password="pass123",
            role=UserRole.SUPER_ADMIN.value,
        )
        merchant_user = CustomUser.objects.create_user(
            username="merchant",
            email="merchant@example.com",
            password="pass123",
            role=UserRole.MERCHANT.value,
        )
        driver_user = CustomUser.objects.create_user(
            username="driver1",
            email="driver@example.com",
            password="pass123",
            role=UserRole.DRIVER.value,
        )
        store = create_test_store(merchant_user)

        DailySalesReport.objects.create(
            report_date="2026-06-01",
            store=store,
            order_count=3,
            gross_revenue="200000.00",
        )
        DriverCommission.objects.create(
            report_date="2026-06-01",
            driver=driver_user,
            delivery_count=2,
            commission_amount="5000.00",
        )

        client = APIClient()
        client.force_authenticate(user=super_admin)
        response = client.get("/api/v1/analytics/commissions/")

        assert response.status_code == status.HTTP_200_OK
        payload = response.json()
        assert len(payload["store_sales"]) == 1
        assert payload["store_sales"][0]["store_name"] == "Tienda Test"
        assert payload["store_sales"][0]["order_count"] == 3
        assert payload["store_sales"][0]["gross_revenue"] == "200000.00"

        assert len(payload["driver_commissions"]) == 1
        assert payload["driver_commissions"][0]["driver_username"] == "driver1"
        assert payload["driver_commissions"][0]["driver_email"] == "driver@example.com"
        assert payload["driver_commissions"][0]["delivery_count"] == 2
        assert payload["driver_commissions"][0]["commission_amount"] == "5000.00"


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_admin_commissions_list_forbidden_for_merchant():
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        merchant_user = CustomUser.objects.create_user(
            username="merchant",
            email="merchant@example.com",
            password="pass123",
            role=UserRole.MERCHANT.value,
        )

        client = APIClient()
        client.force_authenticate(user=merchant_user)
        response = client.get("/api/v1/analytics/commissions/")

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_admin_commissions_export_returns_csv():
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.analytics.infrastructure.models import (
            DailySalesReport,
            DriverCommission,
        )
        from tests.gis_helpers import create_test_store

        super_admin = CustomUser.objects.create_user(
            username="superadmin",
            email="super@example.com",
            password="pass123",
            role=UserRole.SUPER_ADMIN.value,
        )
        merchant_user = CustomUser.objects.create_user(
            username="merchant",
            email="merchant@example.com",
            password="pass123",
            role=UserRole.MERCHANT.value,
        )
        driver_user = CustomUser.objects.create_user(
            username="driver1",
            email="driver@example.com",
            password="pass123",
            role=UserRole.DRIVER.value,
        )
        store = create_test_store(merchant_user)

        DailySalesReport.objects.create(
            report_date="2026-06-01",
            store=store,
            order_count=1,
            gross_revenue="100000.00",
        )
        DriverCommission.objects.create(
            report_date="2026-06-01",
            driver=driver_user,
            delivery_count=1,
            commission_amount="2500.00",
        )

        client = APIClient()
        client.force_authenticate(user=super_admin)
        response = client.get("/api/v1/analytics/commissions/export/")

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"
        assert 'attachment; filename="commissions_report.csv"' in response[
            "Content-Disposition"
        ]

        content = response.content.decode("utf-8")
        assert "Ventas por comercio" in content
        assert "Tienda Test" in content
        assert "Comisiones por conductor" in content
        assert "driver1" in content
        assert "driver@example.com" in content
