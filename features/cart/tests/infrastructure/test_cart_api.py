from decimal import Decimal
from pathlib import Path

import pytest
from django.test.utils import override_settings
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, CustomerProfile
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
        "TEST": {"NAME": "test_dts_cart_api"},
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


def _customer(username: str) -> CustomUser:
    user = CustomUser.objects.create_user(
        username=username,
        email=f"{username}@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )
    CustomerProfile.objects.create(user=user, phone="+573001112233")
    return user


@pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_cart_crud_flow(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.cart.infrastructure.models import Cart, CartItem
        from features.products.infrastructure.models import Product
        from features.stores.infrastructure.models import Store

        customer = _customer("cart_crud")
        other = _customer("cart_other")
        merchant = CustomUser.objects.create_user(
            username="cart_merchant",
            email="cart_merchant@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = Store(owner=merchant, name="Tienda Cart", status=StoreStatus.OPEN)
        store.set_location(GeoLocation(latitude=4.7110, longitude=-74.0721))
        store.save()
        store2 = Store(owner=merchant, name="Otra", status=StoreStatus.OPEN)
        store2.set_location(GeoLocation(latitude=4.72, longitude=-74.08))
        store2.save()

        product = Product.objects.create(
            store=store,
            name="Pizza",
            price=Decimal("12000"),
            stock=10,
            product_type=ProductType.PHYSICAL,
            is_active=True,
        )
        product2 = Product.objects.create(
            store=store2,
            name="Sushi",
            price=Decimal("20000"),
            stock=5,
            product_type=ProductType.PHYSICAL,
            is_active=True,
        )

        _auth(api_client, customer)
        empty = api_client.get("/api/v1/cart/")
        assert empty.status_code == status.HTTP_200_OK
        assert empty.data["items"] == []

        add = api_client.post(
            "/api/v1/cart/items/",
            {"product_id": product.id, "quantity": 2, "notes": "sin cebolla"},
            format="json",
        )
        assert add.status_code == status.HTTP_200_OK
        assert add.data["store_id"] == store.id
        assert add.data["item_count"] == 2

        patched = api_client.patch(
            f"/api/v1/cart/items/{product.id}/",
            {"quantity": 5},
            format="json",
        )
        assert patched.status_code == status.HTTP_200_OK
        assert patched.data["item_count"] == 5

        replaced = api_client.post(
            "/api/v1/cart/items/",
            {"product_id": product2.id, "quantity": 1, "replace_store": True},
            format="json",
        )
        assert replaced.status_code == status.HTTP_200_OK
        assert replaced.data["store_id"] == store2.id
        assert len(replaced.data["items"]) == 1

        _auth(api_client, other)
        other_cart = api_client.get("/api/v1/cart/")
        assert other_cart.data["items"] == []
        assert CartItem.objects.filter(cart__user=customer).count() == 1

        _auth(api_client, customer)
        cleared = api_client.delete("/api/v1/cart/")
        assert cleared.status_code == status.HTTP_204_NO_CONTENT
        assert Cart.objects.get(user=customer).store_id is None
        assert CartItem.objects.filter(cart__user=customer).count() == 0
