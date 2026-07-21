import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, CustomerProfile


def _auth(api_client, user):
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


def _create_customer(username: str = "customer_profile") -> CustomUser:
    user = CustomUser.objects.create_user(
        username=username,
        email=f"{username}@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )
    CustomerProfile.objects.create(
        user=user,
        phone="+573001112233",
        default_address="Calle 1 # 2-3",
    )
    return user


@pytest.mark.django_db
def test_get_customer_profile(api_client):
    customer = _create_customer()
    _auth(api_client, customer)

    response = api_client.get("/api/v1/accounts/customer/profile/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["phone"] == "+573001112233"
    assert response.data["default_address"] == "Calle 1 # 2-3"
    assert response.data["full_name"] == "customer_profile"


@pytest.mark.django_db
def test_patch_customer_profile(api_client):
    customer = _create_customer("customer_patch")
    _auth(api_client, customer)

    response = api_client.patch(
        "/api/v1/accounts/customer/profile/",
        {
            "full_name": "Ana Cliente",
            "phone": "+573009998877",
            "photo_url": "https://cdn.example.com/photo.jpg",
            "default_address": "Calle 50 # 10-20",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["full_name"] == "Ana Cliente"
    assert response.data["phone"] == "+573009998877"
    assert response.data["photo_url"] == "https://cdn.example.com/photo.jpg"
    assert response.data["default_address"] == "Calle 50 # 10-20"


@pytest.mark.django_db
def test_customer_profile_forbidden_for_driver(api_client):
    user = CustomUser.objects.create_user(
        username="driver_not_customer",
        email="driver_not_customer@test.com",
        password="securepass123",
        role=UserRole.DRIVER,
    )
    _auth(api_client, user)

    response = api_client.get("/api/v1/accounts/customer/profile/")
    assert response.status_code == status.HTTP_403_FORBIDDEN
