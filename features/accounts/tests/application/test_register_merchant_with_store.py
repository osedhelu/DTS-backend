from pathlib import Path

import pytest
from django.test.utils import override_settings

from core.settings.apps_registry import build_installed_apps

BACKEND_DIR = Path(__file__).resolve().parents[4]

POSTGIS_DATABASE = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "dts_delivery",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {"NAME": "test_dts_merchant_register"},
    }
}


def _geos_available() -> bool:
    try:
        from django.contrib.gis.gdal import GDAL_VERSION  # noqa: F401
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
def test_merchant_register_creates_store_and_categories():
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.accounts.application.dto import RegisterMerchantWithStoreDTO
        from features.accounts.application.use_cases.register_merchant_with_store import (
            RegisterMerchantWithStoreUseCase,
        )
        from features.accounts.domain.entities import UserRole
        from features.accounts.infrastructure.models import CustomUser, MerchantProfile
        from features.accounts.infrastructure.repositories import DjangoUserRepository
        from features.accounts.infrastructure.verification_token_repository import (
            DjangoEmailVerificationTokenRepository,
        )
        from features.products.infrastructure.models import Category
        from features.stores.domain.entities import StoreVertical
        from features.stores.infrastructure.models import Store
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        use_case = RegisterMerchantWithStoreUseCase(
            user_exists_checker=DjangoUserRepository().exists_by_email,
            store_repository=DjangoStoreRepository(),
            token_repository=DjangoEmailVerificationTokenRepository(),
        )
        result = use_case.execute(
            RegisterMerchantWithStoreDTO(
                email="newmerchant@test.com",
                password="securepass123",
                first_name="Ana",
                last_name="López",
                store_name="Burger Ana",
                vertical=StoreVertical.FOOD,
                category_template="Comida rápida",
                phone="+573001112233",
                latitude=4.711,
                longitude=-74.0721,
            )
        )

        user = CustomUser.objects.get(pk=result.user_id)
        assert user.role == UserRole.MERCHANT
        assert user.email_verified is False
        assert user.is_active is False
        assert MerchantProfile.objects.filter(user=user, business_name="Burger Ana").exists()

        store = Store.objects.get(pk=result.store_id)
        assert store.name == "Burger Ana"
        assert store.vertical == StoreVertical.FOOD
        assert store.owner_id == user.id
        assert store.latitude == pytest.approx(4.711)
        assert store.longitude == pytest.approx(-74.0721)

        categories = Category.objects.filter(store=store).order_by("name")
        assert categories.count() == 4
        parent = categories.filter(parent__isnull=True).get()
        assert parent.name == "Comida rápida"
        assert categories.filter(parent=parent).count() == 3

        assert result.verification_token
