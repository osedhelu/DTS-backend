from decimal import Decimal
from pathlib import Path

import pytest
from django.test.utils import override_settings

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser
from features.products.application.dto import ProductVariantInput, UpdateProductDTO
from features.products.application.use_cases.update_product import UpdateProductUseCase
from features.products.domain.entities import ProductType
from features.products.domain.exceptions import VariantsNotAllowedError
from features.stores.domain.entities import StoreVertical
from tests.gis_helpers import POSTGIS_DATABASE, create_test_store, postgis_tests_available

BACKEND_DIR = Path(__file__).resolve().parents[4]


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_update_product_with_variants():
    from features.products.infrastructure.repositories import (
        DjangoCategoryRepository,
        DjangoProductRepository,
    )
    from features.stores.infrastructure.models import Store as StoreModel
    from features.stores.infrastructure.repositories import DjangoStoreRepository

    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        merchant = CustomUser.objects.create_user(
            username="merchant_update_variants",
            email="update_variants@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = create_test_store(merchant)
        StoreModel.objects.filter(pk=store.pk).update(vertical=StoreVertical.FOOD)

        product_repository = DjangoProductRepository()
        product = product_repository.create(
            {
                "store_id": store.pk,
                "name": "Hamburguesa clásica",
                "price": Decimal("15990.00"),
                "stock": 10,
                "product_type": ProductType.PHYSICAL,
            }
        )

        use_case = UpdateProductUseCase(
            product_repository,
            DjangoCategoryRepository(),
            DjangoStoreRepository(),
        )
        details = use_case.execute(
            UpdateProductDTO(
                product_id=product.id,
                owner_id=merchant.id,
                name="Hamburgua premium",
                variants=[
                    ProductVariantInput(name="S", price=Decimal("12990"), sort_order=0),
                    ProductVariantInput(name="L", price=Decimal("18990"), sort_order=1),
                ],
                ingredients=[],
            )
        )

        assert details.product.name == "Hamburgua premium"
        assert len(details.variants) == 2
        assert details.variants[0].name == "S"
        assert details.variants[1].price == Decimal("18990")


@pytest.mark.skipif(
    not postgis_tests_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)
@pytest.mark.django_db
def test_service_product_rejects_variants():
    from features.products.infrastructure.repositories import (
        DjangoCategoryRepository,
        DjangoProductRepository,
    )
    from features.stores.infrastructure.models import Store as StoreModel
    from features.stores.infrastructure.repositories import DjangoStoreRepository

    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        merchant = CustomUser.objects.create_user(
            username="merchant_service_variants",
            email="service_variants@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        store = create_test_store(merchant)
        StoreModel.objects.filter(pk=store.pk).update(vertical=StoreVertical.SERVICES)

        product_repository = DjangoProductRepository()
        product = product_repository.create(
            {
                "store_id": store.pk,
                "name": "Limpieza profunda",
                "price": Decimal("85000.00"),
                "stock": 0,
                "product_type": ProductType.SERVICE,
                "requires_on_site_visit": True,
                "duration_minutes": 180,
            }
        )

        use_case = UpdateProductUseCase(
            product_repository,
            DjangoCategoryRepository(),
            DjangoStoreRepository(),
        )

        with pytest.raises(VariantsNotAllowedError):
            use_case.execute(
                UpdateProductDTO(
                    product_id=product.id,
                    owner_id=merchant.id,
                    variants=[
                        ProductVariantInput(name="Básico", price=Decimal("70000")),
                    ],
                )
            )
