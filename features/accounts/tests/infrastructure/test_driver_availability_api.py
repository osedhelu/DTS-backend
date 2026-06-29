import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, DriverProfile


def _auth(api_client, user):
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


def _create_driver(username: str = "driver_avail") -> CustomUser:
    user = CustomUser.objects.create_user(
        username=username,
        email=f"{username}@test.com",
        password="securepass123",
        role=UserRole.DRIVER,
    )
    DriverProfile.objects.create(
        user=user,
        phone="+573001112233",
        license_number="LIC-001",
        vehicle_type="moto",
        is_online=False,
    )
    return user


@pytest.mark.django_db
def test_driver_toggle_online(api_client):
    driver = _create_driver()
    _auth(api_client, driver)

    response = api_client.patch(
        "/api/v1/accounts/driver/availability/",
        {"is_online": True},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["is_online"] is True
    driver.driver_profile.refresh_from_db()
    assert driver.driver_profile.is_online is True


@pytest.mark.django_db
def test_driver_updates_location(api_client):
    driver = _create_driver("driver_gps")
    _auth(api_client, driver)

    response = api_client.patch(
        "/api/v1/accounts/driver/availability/",
        {
            "is_online": True,
            "latitude": 4.711,
            "longitude": -74.072,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["latitude"] == pytest.approx(4.711)
    assert response.data["longitude"] == pytest.approx(-74.072)
    driver.driver_profile.refresh_from_db()
    assert driver.driver_profile.last_latitude == pytest.approx(4.711)
    assert driver.driver_profile.last_longitude == pytest.approx(-74.072)


@pytest.mark.django_db
def test_driver_availability_forbidden_for_customer(api_client):
    user = CustomUser.objects.create_user(
        username="customer_avail",
        email="customer_avail@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )
    _auth(api_client, user)

    response = api_client.patch(
        "/api/v1/accounts/driver/availability/",
        {"is_online": True},
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
