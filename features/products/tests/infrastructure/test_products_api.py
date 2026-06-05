from decimal import Decimal
from pathlib import Path

import pytest
from django.test.utils import override_settings
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
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
        "TEST": {"NAME": "test_dts_products_api"},
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


def _create_store(owner, name="Tienda Catálogo"):
    from features.stores.infrastructure.models import Store as StoreModel

    store = StoreModel(owner=owner, name=name, status=StoreStatus.OPEN)
    store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
    store.save()
    return store


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_list_products_by_store(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.products.infrastructure.models import Category, Product

        merchant = CustomUser.objects.create_user(
            username="merchant_products",
            email="products@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = _create_store(merchant)
        root = Category.objects.create(store=store, name="Comida")
        sub = Category.objects.create(store=store, name="Hamburguesas", parent=root)

        Product.objects.create(
            store=store,
            category=root,
            subcategory=sub,
            name="Clásica",
            price=Decimal("15990"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )
        Product.objects.create(
            store=store,
            category=root,
            name="Inactiva",
            price=Decimal("1000"),
            is_active=False,
            product_type=ProductType.PHYSICAL,
        )

        response = api_client.get(f"/api/v1/stores/{store.id}/products/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Clásica"
        assert response.data[0]["product_type"] == ProductType.PHYSICAL

        filtered = api_client.get(
            f"/api/v1/stores/{store.id}/products/",
            {"subcategory": sub.id},
        )
        assert len(filtered.data) == 1
        assert filtered.data[0]["subcategory_id"] == sub.id


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_list_categories_tree(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.products.infrastructure.models import Category

        merchant = CustomUser.objects.create_user(
            username="merchant_categories",
            email="categories@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = _create_store(merchant, name="Limpieza Express")
        root = Category.objects.create(store=store, name="Servicios del hogar")
        Category.objects.create(store=store, name="Limpieza", parent=root)

        response = api_client.get(f"/api/v1/stores/{store.id}/categories/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Servicios del hogar"
        assert len(response.data[0]["subcategories"]) == 1
        assert response.data[0]["subcategories"][0]["name"] == "Limpieza"


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_unauthorized_crud(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        merchant = CustomUser.objects.create_user(
            username="merchant_owner",
            email="owner@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_crud",
            email="customer@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        store = _create_store(merchant)

        _auth(api_client, customer)
        create_product = api_client.post(
            f"/api/v1/stores/{store.id}/products/",
            {"name": "No permitido", "price": "1000"},
            format="json",
        )
        assert create_product.status_code == status.HTTP_403_FORBIDDEN

        create_category = api_client.post(
            f"/api/v1/stores/{store.id}/categories/",
            {"name": "No permitida"},
            format="json",
        )
        assert create_category.status_code == status.HTTP_403_FORBIDDEN

        other_merchant = CustomUser.objects.create_user(
            username="other_merchant",
            email="other@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        _auth(api_client, other_merchant)
        create_other = api_client.post(
            f"/api/v1/stores/{store.id}/products/",
            {"name": "Ajeno", "price": "5000"},
            format="json",
        )
        assert create_other.status_code == status.HTTP_403_FORBIDDEN
