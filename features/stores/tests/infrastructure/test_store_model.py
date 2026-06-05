from pathlib import Path

import pytest
from django.test.utils import override_settings

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
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
        "TEST": {"NAME": "test_dts_stores"},
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
def test_store_save_with_location():
    from features.stores.infrastructure.models import Store

    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        owner = CustomUser.objects.create_user(
            username="merchant_store",
            email="store@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        geo = GeoLocation(latitude=4.7110, longitude=-74.0721)

        store = Store(
            owner=owner,
            name="Restaurante Central",
            status=StoreStatus.OPEN,
            address="Calle 100 #15-20",
        )
        store.set_location(geo)
        store.save()

        saved = Store.objects.get(pk=store.pk)
        assert saved.name == "Restaurante Central"
        assert saved.latitude == pytest.approx(4.7110)
        assert saved.longitude == pytest.approx(-74.0721)
        assert saved.status == StoreStatus.OPEN
