from decimal import Decimal
from pathlib import Path

import pytest
from django.test.utils import override_settings
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.settings.apps_registry import build_installed_apps
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import (
    CustomUser,
    CustomerProfile,
    DriverProfile,
)
from features.orders.domain.value_objects import OrderStatus, OrderType
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
        "TEST": {"NAME": "test_dts_work_search_radii"},
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


requires_geos = pytest.mark.skipif(
    not _geos_available(),
    reason="GDAL/GEOS requerido. Instala: brew install gdal geos && make docker-up",
)


@requires_geos
@pytest.mark.django_db
def test_driver_patch_work_zone(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        driver = CustomUser.objects.create_user(
            username="driver_zone",
            email="driver_zone@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
        )
        DriverProfile.objects.create(
            user=driver,
            phone="+573001111111",
            last_latitude=4.71,
            last_longitude=-74.07,
        )
        _auth(api_client, driver)

        response = api_client.patch(
            "/api/v1/accounts/driver/profile/",
            {
                "work_center_latitude": 4.65,
                "work_center_longitude": -74.08,
                "work_radius_km": 35,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["work_center_latitude"] == 4.65
        assert response.data["work_center_longitude"] == -74.08
        assert float(response.data["work_radius_km"]) == 35.0

        profile = DriverProfile.objects.get(user=driver)
        assert profile.work_center_latitude == 4.65
        assert float(profile.work_radius_km) == 35.0


@requires_geos
@pytest.mark.django_db
def test_list_driver_offers_respects_work_radius(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.delivery.application.use_cases.list_driver_offers import (
            ListDriverOffersUseCase,
        )
        from features.orders.infrastructure.models import Order
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_offers_zone",
            email="merchant_offers_zone@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_offers_zone",
            email="customer_offers_zone@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        driver = CustomUser.objects.create_user(
            username="driver_offers_zone",
            email="driver_offers_zone@test.com",
            password="securepass123",
            role=UserRole.DRIVER,
        )
        DriverProfile.objects.create(
            user=driver,
            phone="+573002222222",
            is_online=True,
            last_latitude=5.0,
            last_longitude=-74.0,
            work_center_latitude=4.7100,
            work_center_longitude=-74.0720,
            work_radius_km=10.0,
        )

        near_store = Store(owner=merchant, name="Near Store", status=StoreStatus.OPEN)
        near_store.set_location(GeoLocation(latitude=4.7200, longitude=-74.0720))
        near_store.save()

        far_store = Store(owner=merchant, name="Far Store", status=StoreStatus.OPEN)
        far_store.set_location(GeoLocation(latitude=4.9000, longitude=-74.0720))
        far_store.save()

        Order.objects.create(
            customer=customer,
            store=near_store,
            status=OrderStatus.SEARCHING_DRIVER,
            order_type=OrderType.DELIVERY,
            total=Decimal("20.00"),
        )
        Order.objects.create(
            customer=customer,
            store=far_store,
            status=OrderStatus.SEARCHING_DRIVER,
            order_type=OrderType.DELIVERY,
            total=Decimal("30.00"),
        )

        offers = ListDriverOffersUseCase().execute(driver.id)
        assert len(offers) == 1
        assert offers[0].store_name == "Near Store"


@requires_geos
@pytest.mark.django_db
def test_customer_stores_filtered_by_radius(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        from features.stores.infrastructure.models import Store

        merchant = CustomUser.objects.create_user(
            username="merchant_search_radius",
            email="merchant_search_radius@test.com",
            password="securepass123",
            role=UserRole.MERCHANT,
        )
        customer = CustomUser.objects.create_user(
            username="customer_search_radius",
            email="customer_search_radius@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        CustomerProfile.objects.create(user=customer, phone="+573003333333")

        near = Store(owner=merchant, name="Tienda Cerca", status=StoreStatus.OPEN)
        near.set_location(GeoLocation(latitude=4.7100, longitude=-74.0720))
        near.save()

        far = Store(owner=merchant, name="Tienda Lejos", status=StoreStatus.OPEN)
        far.set_location(GeoLocation(latitude=4.9000, longitude=-74.0720))
        far.save()

        _auth(api_client, customer)
        response = api_client.get(
            "/api/v1/stores/",
            {
                "latitude": "4.7100",
                "longitude": "-74.0720",
                "radius_km": "5",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        names = {item["name"] for item in response.data["results"]}
        assert "Tienda Cerca" in names
        assert "Tienda Lejos" not in names


@requires_geos
@pytest.mark.django_db
def test_customer_stores_invalid_radius_returns_400(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        customer = CustomUser.objects.create_user(
            username="customer_bad_radius",
            email="customer_bad_radius@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        CustomerProfile.objects.create(user=customer, phone="+573004444444")
        _auth(api_client, customer)

        response = api_client.get(
            "/api/v1/stores/",
            {
                "latitude": "4.71",
                "longitude": "-74.07",
                "radius_km": "9999",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@requires_geos
@pytest.mark.django_db
def test_customer_patch_search_radius(api_client):
    with override_settings(
        DATABASES=POSTGIS_DATABASE,
        INSTALLED_APPS=build_installed_apps(BACKEND_DIR),
    ):
        customer = CustomUser.objects.create_user(
            username="customer_patch_search",
            email="customer_patch_search@test.com",
            password="securepass123",
            role=UserRole.CUSTOMER,
        )
        CustomerProfile.objects.create(user=customer, phone="+573005555555")
        _auth(api_client, customer)

        response = api_client.patch(
            "/api/v1/accounts/customer/profile/",
            {
                "search_center_latitude": 4.65,
                "search_center_longitude": -74.08,
                "search_radius_km": 20,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["search_center_latitude"] == 4.65
        assert float(response.data["search_radius_km"]) == 20.0
