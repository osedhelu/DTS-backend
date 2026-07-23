from unittest.mock import MagicMock

import pytest
from rest_framework_simplejwt.tokens import AccessToken

from features.accounts.application.use_cases.apple_sign_in import AppleSignInUseCase
from features.accounts.application.use_cases.google_sign_in import GoogleSignInUseCase
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.firebase_token_verifier import VerifiedSocialIdentity
from features.accounts.infrastructure.models import (
    CustomUser,
    CustomerProfile,
    DriverProfile,
)


@pytest.mark.django_db
def test_google_signin_usecase_creates_driver():
    verifier = MagicMock()
    verifier.verify_google_id_token.return_value = VerifiedSocialIdentity(
        uid="g-driver",
        email="gdriver@test.com",
        display_name="G Driver",
        provider="google",
    )
    tokens = GoogleSignInUseCase(verifier).execute("tok", role=UserRole.DRIVER)
    assert "access" in tokens
    user = CustomUser.objects.get(email="gdriver@test.com")
    assert user.role == UserRole.DRIVER
    assert DriverProfile.objects.filter(user=user).exists()
    claims = AccessToken(tokens["access"])
    assert claims["role"] == UserRole.DRIVER
    assert claims["user_id"] == user.id


@pytest.mark.django_db
def test_google_signin_relinks_google_uid_on_firebase_migration():
    """Mismo email+rol con UID nuevo (migración Firebase) debe revinclar, no 400."""
    user = CustomUser.objects.create_user(
        username="migrate_me",
        email="migrate@test.com",
        password="x",
        role=UserRole.CUSTOMER,
    )
    user.google_uid = "old-firebase-uid"
    user.auth_provider = "google"
    user.save(update_fields=["google_uid", "auth_provider"])

    verifier = MagicMock()
    verifier.verify_google_id_token.return_value = VerifiedSocialIdentity(
        uid="new-dtsdrop-uid",
        email="migrate@test.com",
        display_name="Migrated",
        provider="google",
    )
    tokens = GoogleSignInUseCase(verifier).execute("tok", role=UserRole.CUSTOMER)
    assert "access" in tokens
    user.refresh_from_db()
    assert user.google_uid == "new-dtsdrop-uid"


@pytest.mark.django_db
def test_apple_signin_usecase_creates_driver():
    verifier = MagicMock()
    verifier.verify_apple_id_token.return_value = VerifiedSocialIdentity(
        uid="a-driver",
        email="adriver@test.com",
        display_name="A Driver",
        provider="apple",
    )
    tokens = AppleSignInUseCase(verifier).execute("tok", role=UserRole.DRIVER)
    assert "access" in tokens
    user = CustomUser.objects.get(email="adriver@test.com")
    assert user.apple_uid == "a-driver"
    assert DriverProfile.objects.filter(user=user).exists()
    claims = AccessToken(tokens["access"])
    assert claims["role"] == UserRole.DRIVER
    assert claims["email"] == "adriver@test.com"


@pytest.mark.django_db
def test_apple_signin_usecase_placeholder_email_when_missing():
    verifier = MagicMock()
    verifier.verify_apple_id_token.return_value = VerifiedSocialIdentity(
        uid="a-no-email",
        email=None,
        display_name="anon",
        provider="apple",
    )
    tokens = AppleSignInUseCase(verifier).execute("tok", role=UserRole.DRIVER)
    user = CustomUser.objects.get(apple_uid="a-no-email")
    assert user.email == "a-no-email@privaterelay.appleid.local"
    assert AccessToken(tokens["access"])["role"] == UserRole.DRIVER
