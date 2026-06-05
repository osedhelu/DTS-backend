import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser


def _auth_client(api_client, user):
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


@pytest.mark.django_db
def test_merchant_cannot_access_admin(api_client):
    merchant = CustomUser.objects.create_user(
        username="merchant1",
        email="merchant@test.com",
        password="securepass123",
        role=UserRole.MERCHANT,
    )
    _auth_client(api_client, merchant)

    response = api_client.get("/api/v1/accounts/admin/dashboard/")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_super_admin_can_access_admin_dashboard(api_client):
    admin = CustomUser.objects.create_superuser(
        username="superadmin",
        email="admin@test.com",
        password="securepass123",
    )
    _auth_client(api_client, admin)

    response = api_client.get("/api/v1/accounts/admin/dashboard/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["detail"] == "Panel super admin"
