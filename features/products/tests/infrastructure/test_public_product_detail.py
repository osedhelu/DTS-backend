from decimal import Decimal
from pathlib import Path

import pytest
from django.test.utils import override_settings
from rest_framework import status

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.products.domain.entities import ProductType
from features.products.infrastructure.models import Category, Product
from features.stores.domain.entities import StoreStatus
from features.stores.domain.value_objects import GeoLocation
from features.stores.infrastructure.models import Store

BACKEND_DIR = Path(__file__).resolve().parents[4]

POSTGIS_DATABASE = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "dts_delivery",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {"NAME": "test_dts_public_product"},
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
def test_public_product_detail(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        merchant = CustomUser.objects.create_user(
            username="merchant_public_product",
            email="merchant_public_product@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )

        store = Store(
            owner=merchant,
            name="Lavandería Pública",
            status=StoreStatus.OPEN,
        )
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()

        category = Category.objects.create(
            store=store,
            name="Lavandería",
            field_config={"kg": "texto_libre"},
        )
        product = Product.objects.create(
            store=store,
            category=category,
            name="Lavado express",
            price=Decimal("35000.00"),
            stock=0,
            product_type=ProductType.SERVICE,
            duration_minutes=90,
            description="Servicio a domicilio",
            is_active=True,
        )

        response = api_client.get(
            f"/api/v1/stores/{store.id}/products/{product.id}/public/",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == product.id
        assert response.data["name"] == "Lavado express"
        assert response.data["product_type"] == ProductType.SERVICE
        assert response.data["duration_minutes"] == 90
        assert response.data["field_config"] == {"kg": "texto_libre"}
        assert "images" in response.data

        inactive = Product.objects.create(
            store=store,
            name="Servicio inactivo",
            price=Decimal("10000.00"),
            stock=0,
            product_type=ProductType.SERVICE,
            is_active=False,
        )
        hidden = api_client.get(
            f"/api/v1/stores/{store.id}/products/{inactive.id}/public/",
        )
        assert hidden.status_code == status.HTTP_404_NOT_FOUND
