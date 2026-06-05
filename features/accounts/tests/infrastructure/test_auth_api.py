import pytest
from rest_framework import status

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, MerchantProfile


@pytest.mark.django_db
def test_register_201(api_client):
    payload = {
        "username": "merchant_shop",
        "email": "shop@test.com",
        "password": "securepass123",
        "role": UserRole.MERCHANT,
        "phone": "+573001112233",
        "business_name": "Restaurante El Buen Sabor",
        "tax_id": "900123456",
        "address": "Calle 10 #20-30",
    }

    response = api_client.post("/api/v1/accounts/register/", payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["email"] == "shop@test.com"
    assert response.data["role"] == UserRole.MERCHANT
    assert CustomUser.objects.filter(email="shop@test.com").exists()
    assert MerchantProfile.objects.filter(business_name="Restaurante El Buen Sabor").exists()


@pytest.mark.django_db
def test_login_returns_token(api_client):
    CustomUser.objects.create_user(
        username="loginuser",
        email="login@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )

    response = api_client.post(
        "/api/v1/accounts/login/",
        {"username": "loginuser", "password": "securepass123"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data
