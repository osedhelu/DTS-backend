import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, DeviceToken


def _auth(api_client, user):
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


@pytest.mark.django_db
def test_register_device_token(api_client):
    user = CustomUser.objects.create_user(
        username="customer_fcm",
        email="customer_fcm@test.com",
        password="securepass123",
        role=UserRole.CUSTOMER,
    )

    _auth(api_client, user)
    response = api_client.post(
        "/api/v1/accounts/device-token/",
        {"token": "fcm-token-abc123", "platform": "android"},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["token"] == "fcm-token-abc123"
    assert response.data["platform"] == "android"
    assert response.data["is_active"] is True
    assert DeviceToken.objects.filter(user=user, token="fcm-token-abc123").exists()

    update_response = api_client.post(
        "/api/v1/accounts/device-token/",
        {"token": "fcm-token-abc123", "platform": "ios"},
        format="json",
    )
    assert update_response.status_code == status.HTTP_201_CREATED
    assert update_response.data["platform"] == "ios"
    assert DeviceToken.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_unregister_device_token(api_client):
    user = CustomUser.objects.create_user(
        username="driver_fcm",
        email="driver_fcm@test.com",
        password="securepass123",
        role=UserRole.DRIVER,
    )
    DeviceToken.objects.create(
        user=user,
        token="fcm-token-to-remove",
        platform="android",
    )

    _auth(api_client, user)
    response = api_client.delete(
        "/api/v1/accounts/device-token/",
        {"token": "fcm-token-to-remove"},
        format="json",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not DeviceToken.objects.filter(user=user, token="fcm-token-to-remove").exists()

    missing = api_client.delete(
        "/api/v1/accounts/device-token/",
        {"token": "unknown-token"},
        format="json",
    )
    assert missing.status_code == status.HTTP_404_NOT_FOUND
