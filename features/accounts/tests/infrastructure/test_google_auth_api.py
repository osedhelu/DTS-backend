from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.firebase_token_verifier import VerifiedGoogleIdentity
from features.accounts.infrastructure.models import CustomUser, CustomerProfile


@pytest.mark.django_db
def test_google_signin_creates_customer(api_client):
    identity = VerifiedGoogleIdentity(
        uid="google-uid-123",
        email="newgoogle@test.com",
        display_name="Nuevo Google",
    )

    with patch(
        "features.accounts.application.use_cases.google_sign_in.FirebaseTokenVerifier"
    ) as verifier_cls:
        verifier_cls.return_value.verify_google_id_token.return_value = identity
        response = api_client.post(
            "/api/v1/accounts/auth/google/",
            {"id_token": "valid-token"},
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data
    claims = AccessToken(response.data["access"])
    assert claims["role"] == UserRole.CUSTOMER
    assert claims["email"] == "newgoogle@test.com"
    assert claims["user_id"] == CustomUser.objects.get(email="newgoogle@test.com").id
    user = CustomUser.objects.get(email="newgoogle@test.com")
    assert user.role == UserRole.CUSTOMER
    assert user.google_uid == "google-uid-123"
    assert user.auth_provider == "google"
    assert CustomerProfile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_google_signin_returns_jwt_for_existing_user(api_client):
    user = CustomUser.objects.create_user(
        username="google_existing",
        email="existing@test.com",
        password="unused",
        role=UserRole.CUSTOMER,
        google_uid="google-uid-999",
        auth_provider="google",
        email_verified=True,
    )
    user.set_unusable_password()
    user.save()
    CustomerProfile.objects.create(user=user, phone="+573001112233")

    identity = VerifiedGoogleIdentity(
        uid="google-uid-999",
        email="existing@test.com",
        display_name="Existente",
    )

    with patch(
        "features.accounts.application.use_cases.google_sign_in.FirebaseTokenVerifier"
    ) as verifier_cls:
        verifier_cls.return_value.verify_google_id_token.return_value = identity
        response = api_client.post(
            "/api/v1/accounts/auth/google/",
            {"id_token": "valid-token"},
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data


@pytest.mark.django_db
def test_google_signin_rejects_invalid_token(api_client):
    from features.accounts.domain.exceptions import InvalidGoogleTokenError

    with patch(
        "features.accounts.application.use_cases.google_sign_in.FirebaseTokenVerifier"
    ) as verifier_cls:
        verifier_cls.return_value.verify_google_id_token.side_effect = (
            InvalidGoogleTokenError("Token de Google inválido")
        )
        response = api_client.post(
            "/api/v1/accounts/auth/google/",
            {"id_token": "bad-token"},
            format="json",
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_google_signin_creates_driver(api_client):
    from features.accounts.infrastructure.models import DriverProfile

    identity = VerifiedGoogleIdentity(
        uid="google-driver-1",
        email="driver.google@test.com",
        display_name="Driver G",
        provider="google",
    )

    with patch(
        "features.accounts.application.use_cases.google_sign_in.FirebaseTokenVerifier"
    ) as verifier_cls:
        verifier_cls.return_value.verify_google_id_token.return_value = identity
        response = api_client.post(
            "/api/v1/accounts/auth/google/",
            {"id_token": "valid-token", "role": "driver"},
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    user = CustomUser.objects.get(email="driver.google@test.com")
    assert user.role == UserRole.DRIVER
    assert DriverProfile.objects.filter(user=user).exists()
    claims = AccessToken(response.data["access"])
    assert claims["role"] == UserRole.DRIVER
    assert claims["user_id"] == user.id
    assert claims["email"] == "driver.google@test.com"
    verifier_cls.return_value.verify_google_id_token.assert_called_with(
        "valid-token", role="driver"
    )


@pytest.mark.django_db
def test_google_signin_rejects_role_conflict(api_client):
    from features.accounts.infrastructure.models import DriverProfile

    user = CustomUser.objects.create_user(
        username="as_customer",
        email="shared@test.com",
        password="unused",
        role=UserRole.CUSTOMER,
        google_uid="google-shared",
        auth_provider="google",
        email_verified=True,
    )
    user.set_unusable_password()
    user.save()
    CustomerProfile.objects.create(user=user, phone="")

    identity = VerifiedGoogleIdentity(
        uid="google-shared",
        email="shared@test.com",
        display_name="Shared",
        provider="google",
    )
    with patch(
        "features.accounts.application.use_cases.google_sign_in.FirebaseTokenVerifier"
    ) as verifier_cls:
        verifier_cls.return_value.verify_google_id_token.return_value = identity
        response = api_client.post(
            "/api/v1/accounts/auth/google/",
            {"id_token": "valid-token", "role": "driver"},
            format="json",
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not DriverProfile.objects.filter(user=user).exists()
