from pathlib import Path

import pytest
from django.test.utils import override_settings

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
        "TEST": {"NAME": "test_dts_products"},
    }
}


def _geos_available() -> bool:
    try:
        from django.contrib.gis.geos import Point

        Point(0, 0, srid=4326)
        return True
    except Exception:
        return False


def _create_store(owner):
    from features.stores.infrastructure.models import Store

    store = Store(
        owner=owner,
        name="Tienda Demo",
        status=StoreStatus.OPEN,
        address="Calle 100",
    )
    store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
    store.save()
    return store


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_product_belongs_to_store():
    from features.products.infrastructure.models import Category, Product

    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        owner = CustomUser.objects.create_user(
            username="merchant_product",
            email="product@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = _create_store(owner)
        root = Category.objects.create(store=store, name="Comida")

        product = Product.objects.create(
            store=store,
            category=root,
            name="Hamburguesa clásica",
            price="15990.00",
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        saved = Product.objects.select_related("store").get(pk=product.pk)
        assert saved.store_id == store.pk
        assert saved.store.name == "Tienda Demo"
        assert saved.name == "Hamburguesa clásica"
        assert saved.product_type == ProductType.PHYSICAL
        assert saved.tracks_stock is True


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_category_subcategory_hierarchy():
    from features.products.infrastructure.models import Category, Product

    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        owner = CustomUser.objects.create_user(
            username="merchant_category",
            email="category@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = _create_store(owner)

        root = Category.objects.create(store=store, name="Servicios del hogar")
        sub = Category.objects.create(store=store, name="Limpieza", parent=root)

        assert root.is_root is True
        assert sub.is_subcategory is True
        assert sub.parent_id == root.pk
        assert list(root.subcategories.all()) == [sub]

        service = Product.objects.create(
            store=store,
            category=root,
            subcategory=sub,
            name="Limpieza profunda",
            price="85000.00",
            product_type=ProductType.SERVICE,
            requires_on_site_visit=True,
            duration_minutes=180,
        )

        saved = Product.objects.select_related("category", "subcategory").get(pk=service.pk)
        assert saved.category.name == "Servicios del hogar"
        assert saved.subcategory.name == "Limpieza"
        assert saved.duration_minutes == 180
        assert saved.tracks_stock is False
