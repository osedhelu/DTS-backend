from unittest.mock import MagicMock, patch

import pytest

from features.accounts.domain.exceptions import InvalidGoogleTokenError
from features.accounts.infrastructure.firebase_token_verifier import FirebaseTokenVerifier


@patch("features.accounts.infrastructure.firebase_token_verifier.ensure_firebase_app")
def test_verifier_uses_role_project_and_succeeds(mock_ensure_app):
    mock_app = MagicMock(name="driver-app")
    mock_ensure_app.return_value = mock_app

    with patch("firebase_admin.auth.verify_id_token") as mock_verify:
        mock_verify.return_value = {
            "uid": "uid-1",
            "email": "driver@test.com",
            "name": "Driver",
            "firebase": {"sign_in_provider": "google.com"},
        }
        identity = FirebaseTokenVerifier().verify_google_id_token(
            "tok", role="driver"
        )

    mock_ensure_app.assert_called_once_with("driver")
    mock_verify.assert_called_once_with("tok", app=mock_app)
    assert identity.uid == "uid-1"
    assert identity.email == "driver@test.com"
    assert identity.provider == "google"


@patch("features.accounts.infrastructure.firebase_token_verifier.ensure_firebase_app")
def test_verifier_does_not_fallback_to_other_project(mock_ensure_app):
    mock_ensure_app.return_value = MagicMock(name="driver-app")

    with patch("firebase_admin.auth.verify_id_token") as mock_verify:
        mock_verify.side_effect = ValueError("wrong project")
        with pytest.raises(InvalidGoogleTokenError, match="Token de Firebase inválido"):
            FirebaseTokenVerifier().verify_google_id_token("tok", role="driver")

    assert mock_verify.call_count == 1
    mock_ensure_app.assert_called_once_with("driver")


@patch("features.accounts.infrastructure.firebase_token_verifier.ensure_firebase_app")
def test_apple_verifier_allows_missing_email(mock_ensure_app):
    mock_ensure_app.return_value = MagicMock()

    with patch("firebase_admin.auth.verify_id_token") as mock_verify:
        mock_verify.return_value = {
            "uid": "apple-uid-1",
            "firebase": {"sign_in_provider": "apple.com"},
        }
        identity = FirebaseTokenVerifier().verify_apple_id_token(
            "tok", role="driver"
        )

    assert identity.uid == "apple-uid-1"
    assert identity.email is None
    assert identity.provider == "apple"


def test_firebase_app_for_role():
    from features.accounts.infrastructure.firebase_apps import (
        FIREBASE_APP_CUSTOMER,
        FIREBASE_APP_DRIVER,
        firebase_app_for_role,
    )

    assert firebase_app_for_role("customer") == FIREBASE_APP_CUSTOMER
    assert firebase_app_for_role("driver") == FIREBASE_APP_DRIVER
