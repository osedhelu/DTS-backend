from unittest.mock import patch

import pytest
from rest_framework import status

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
