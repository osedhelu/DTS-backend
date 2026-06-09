import pytest
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from tests.gis_helpers import POSTGIS_DATABASE, create_test_store, postgis_tests_available

BACKEND_DIR = __import__("pathlib").Path(__file__).resolve().parents[4]

pytestmark = pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/PostGIS requerido",
)


def _auth(client: APIClient, user: CustomUser) -> None:
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


@pytest.mark.django_db
def test_list_category_templates_marks_imported():
    from features.products.infrastructure.models import Category

    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        merchant = CustomUser.objects.create_user(
            username="tpl_merchant",
            email="tpl_merchant@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = create_test_store(merchant, name="Tpl Store")
        Category.objects.create(store=store, name="Restaurante", parent=None)

        client = APIClient()
        _auth(client, merchant)

        response = client.get(f"/api/v1/stores/{store.pk}/category-templates/?q=entrada")

        assert response.status_code == status.HTTP_200_OK
        payload = response.json()
        assert payload["vertical"] == "food"
        names = {item["name"]: item for item in payload["templates"]}
        assert "Restaurante" in names
        assert names["Restaurante"]["already_imported"] is True
        assert "Entradas" in names["Restaurante"]["subcategories"]


@pytest.mark.django_db
def test_import_category_template_creates_tree():
    from features.products.infrastructure.models import Category

    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        merchant = CustomUser.objects.create_user(
            username="import_merchant",
            email="import_merchant@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = create_test_store(merchant, name="Import Store")

        client = APIClient()
        _auth(client, merchant)

        response = client.post(
            f"/api/v1/stores/{store.pk}/categories/import-template/",
            {"template_name": "Restaurante"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["categories_created"] == 4
        assert Category.objects.filter(store=store, parent__isnull=True).count() == 1
        root = Category.objects.get(store=store, name="Restaurante", parent__isnull=True)
        assert root.subcategories.count() == 3


@pytest.mark.django_db
def test_import_category_template_rejects_duplicate():
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        merchant = CustomUser.objects.create_user(
            username="dup_merchant",
            email="dup_merchant@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = create_test_store(merchant, name="Dup Store")

        client = APIClient()
        _auth(client, merchant)

        first = client.post(
            f"/api/v1/stores/{store.pk}/categories/import-template/",
            {"template_name": "Comida rápida"},
            format="json",
        )
        assert first.status_code == status.HTTP_201_CREATED

        second = client.post(
            f"/api/v1/stores/{store.pk}/categories/import-template/",
            {"template_name": "Comida rápida"},
            format="json",
        )
        assert second.status_code == status.HTTP_400_BAD_REQUEST
