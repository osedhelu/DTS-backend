from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.firebase_token_verifier import VerifiedSocialIdentity
from features.accounts.infrastructure.models import CustomUser, DriverProfile


@pytest.mark.django_db
def test_apple_signin_creates_driver(api_client):
    identity = VerifiedSocialIdentity(
        uid="apple-uid-driver-1",
        email="driver.apple@test.com",
        display_name="Driver Apple",
        provider="apple",
    )

    with patch(
        "features.accounts.application.use_cases.apple_sign_in.FirebaseTokenVerifier"
    ) as verifier_cls:
        verifier_cls.return_value.verify_apple_id_token.return_value = identity
        response = api_client.post(
            "/api/v1/accounts/auth/apple/",
            {"id_token": "valid-apple-token", "role": "driver"},
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    user = CustomUser.objects.get(email="driver.apple@test.com")
    assert user.role == UserRole.DRIVER
    assert user.apple_uid == "apple-uid-driver-1"
    assert user.auth_provider == "apple"
    assert DriverProfile.objects.filter(user=user).exists()
    claims = AccessToken(response.data["access"])
    assert claims["role"] == UserRole.DRIVER
    assert claims["user_id"] == user.id
    assert claims["email"] == user.email


@pytest.mark.django_db
def test_apple_signin_existing_user_without_email_in_token(api_client):
    user = CustomUser.objects.create_user(
        username="apple_existing",
        email="existing.apple@test.com",
        password="unused",
        role=UserRole.DRIVER,
        apple_uid="apple-uid-existing",
        auth_provider="apple",
        email_verified=True,
    )
    user.set_unusable_password()
    user.save()
    DriverProfile.objects.create(
        user=user, phone="", license_number="", vehicle_type=""
    )

    identity = VerifiedSocialIdentity(
        uid="apple-uid-existing",
        email=None,
        display_name="apple-uid-existing",
        provider="apple",
    )

    with patch(
        "features.accounts.application.use_cases.apple_sign_in.FirebaseTokenVerifier"
    ) as verifier_cls:
        verifier_cls.return_value.verify_apple_id_token.return_value = identity
        response = api_client.post(
            "/api/v1/accounts/auth/apple/",
            {"id_token": "valid-apple-token", "role": "driver"},
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    claims = AccessToken(response.data["access"])
    assert claims["role"] == UserRole.DRIVER
    assert claims["user_id"] == user.id


@pytest.mark.django_db
def test_apple_signin_first_login_uses_body_email(api_client):
    identity = VerifiedSocialIdentity(
        uid="apple-uid-new",
        email=None,
        display_name="apple-uid-new",
        provider="apple",
    )

    with patch(
        "features.accounts.application.use_cases.apple_sign_in.FirebaseTokenVerifier"
    ) as verifier_cls:
        verifier_cls.return_value.verify_apple_id_token.return_value = identity
        response = api_client.post(
            "/api/v1/accounts/auth/apple/",
            {
                "id_token": "valid-apple-token",
                "role": "driver",
                "email": "first.apple@test.com",
                "full_name": "First Apple",
            },
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    user = CustomUser.objects.get(apple_uid="apple-uid-new")
    assert user.email == "first.apple@test.com"
    assert DriverProfile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_apple_signin_rejects_invalid_token(api_client):
    from features.accounts.domain.exceptions import InvalidGoogleTokenError

    with patch(
        "features.accounts.application.use_cases.apple_sign_in.FirebaseTokenVerifier"
    ) as verifier_cls:
        verifier_cls.return_value.verify_apple_id_token.side_effect = (
            InvalidGoogleTokenError("Token de Firebase inválido")
        )
        response = api_client.post(
            "/api/v1/accounts/auth/apple/",
            {"id_token": "bad", "role": "driver"},
            format="json",
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
