import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, DriverProfile


def _auth(api_client, user):
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


def _create_driver(username: str = "driver_profile") -> CustomUser:
    user = CustomUser.objects.create_user(
        username=username,
        email=f"{username}@test.com",
        password="securepass123",
        role=UserRole.DRIVER,
    )
    DriverProfile.objects.create(
        user=user,
        phone="+573001112233",
        license_number="",
        vehicle_type="",
        is_online=False,
    )
    return user


@pytest.mark.django_db
def test_get_driver_profile(api_client):
    driver = _create_driver()
    _auth(api_client, driver)

    response = api_client.get("/api/v1/accounts/driver/profile/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["phone"] == "+573001112233"
    assert response.data["onboarding_completed"] is False


@pytest.mark.django_db
def test_complete_driver_onboarding(api_client):
    driver = _create_driver("driver_kyc")
    _auth(api_client, driver)

    response = api_client.patch(
        "/api/v1/accounts/driver/profile/",
        {
            "full_name": "Ana Conductora",
            "phone": "+573009998877",
            "vehicle_type": "moto",
            "vehicle_plate": "abc123",
            "license_number": "LIC-99",
            "complete_onboarding": True,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["full_name"] == "Ana Conductora"
    assert response.data["vehicle_plate"] == "ABC123"
    assert response.data["onboarding_completed"] is True
    driver.driver_profile.refresh_from_db()
    assert driver.driver_profile.onboarding_completed_at is not None


@pytest.mark.django_db
def test_complete_onboarding_requires_fields(api_client):
    driver = _create_driver("driver_incomplete")
    _auth(api_client, driver)

    response = api_client.patch(
        "/api/v1/accounts/driver/profile/",
        {"complete_onboarding": True},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "full_name" in response.data["detail"]


@pytest.mark.django_db
def test_driver_profile_forbidden_for_customer(api_client):
    user = CustomUser.objects.create_user(
        username="customer_profile",
        email="customer_profile@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )
    _auth(api_client, user)

    response = api_client.get("/api/v1/accounts/driver/profile/")
    assert response.status_code == status.HTTP_403_FORBIDDEN
