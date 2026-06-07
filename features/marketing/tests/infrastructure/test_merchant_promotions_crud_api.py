from decimal import Decimal
from pathlib import Path

import pytest
from django.test.utils import override_settings
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.marketing.domain.entities import DiscountType
from tests.gis_helpers import POSTGIS_DATABASE, create_test_store, postgis_tests_available

BACKEND_DIR = Path(__file__).resolve().parents[4]


def _auth(api_client, user):
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_merchant_promotions_crud_api(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.products.domain.entities import ProductType
        from features.products.infrastructure.models import Product

        merchant = CustomUser.objects.create_user(
            username="merchant_promotions",
            email="merchant_promotions@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        other_merchant = CustomUser.objects.create_user(
            username="other_promotions",
            email="other_promotions@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )

        store = create_test_store(merchant, name="Promo Store")
        product = Product.objects.create(
            store=store,
            name="Hamburguesa",
            price=Decimal("20000.00"),
            stock=10,
            product_type=ProductType.PHYSICAL,
        )

        _auth(api_client, merchant)
        create_response = api_client.post(
            f"/api/v1/stores/{store.pk}/promotions/",
            {
                "name": "10% en tienda",
                "discount_type": DiscountType.PERCENTAGE.value,
                "discount_value": "10.00",
            },
            format="json",
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        created = create_response.json()
        assert created["name"] == "10% en tienda"
        assert created["discount_type"] == DiscountType.PERCENTAGE.value
        promotion_id = created["id"]

        list_response = api_client.get(f"/api/v1/stores/{store.pk}/promotions/")
        assert list_response.status_code == status.HTTP_200_OK
        assert list_response.json()["count"] == 1

        update_response = api_client.patch(
            f"/api/v1/stores/{store.pk}/promotions/{promotion_id}/",
            {
                "name": "15% en hamburguesa",
                "product_id": product.pk,
                "discount_value": "15.00",
            },
            format="json",
        )
        assert update_response.status_code == status.HTTP_200_OK
        updated = update_response.json()
        assert updated["product_id"] == product.pk
        assert updated["discount_value"] == "15.00"

        deactivate_response = api_client.patch(
            f"/api/v1/stores/{store.pk}/promotions/{promotion_id}/",
            {"is_active": False},
            format="json",
        )
        assert deactivate_response.status_code == status.HTTP_200_OK
        assert deactivate_response.json()["is_active"] is False

        _auth(api_client, other_merchant)
        forbidden = api_client.get(f"/api/v1/stores/{store.pk}/promotions/")
        assert forbidden.status_code == status.HTTP_403_FORBIDDEN
