"""Verificación de ID tokens Firebase contra el proyecto customer o driver."""

from __future__ import annotations

from dataclasses import dataclass

from features.accounts.domain.exceptions import InvalidGoogleTokenError
from features.accounts.infrastructure.firebase_apps import (
    FIREBASE_APP_CUSTOMER,
    ensure_firebase_app,
    firebase_app_for_role,
)


@dataclass(frozen=True, slots=True)
class VerifiedSocialIdentity:
    uid: str
    email: str | None
    display_name: str
    provider: str = "google"  # google | apple | ...


# Compat alias usado por google_sign_in existente
VerifiedGoogleIdentity = VerifiedSocialIdentity


class FirebaseTokenVerifier:
    """Verifica ID tokens Firebase contra el proyecto del role (sin fallback cruzado)."""

    def verify_id_token(
        self,
        id_token: str,
        *,
        role: str = "customer",
        expected_provider: str | None = None,
        allow_missing_email: bool = False,
    ) -> VerifiedSocialIdentity:
        app_name = firebase_app_for_role(role)
        app = ensure_firebase_app(app_name)

        from firebase_admin import auth

        try:
            decoded = auth.verify_id_token(id_token, app=app)
        except Exception as exc:
            raise InvalidGoogleTokenError("Token de Firebase inválido") from exc

        email_raw = decoded.get("email")
        email = str(email_raw).lower() if email_raw else None
        uid = decoded.get("uid") or decoded.get("sub")
        if not uid:
            raise InvalidGoogleTokenError("Token de Firebase sin uid")
        if not email and not allow_missing_email:
            raise InvalidGoogleTokenError("Token de Firebase sin email o uid")

        provider = str(
            decoded.get("firebase", {}).get("sign_in_provider")
            or decoded.get("sign_in_provider")
            or "unknown"
        )
        if provider in ("google.com", "google"):
            provider = "google"
        elif provider in ("apple.com", "apple"):
            provider = "apple"

        if expected_provider and provider != expected_provider:
            raise InvalidGoogleTokenError(
                f"Se esperaba proveedor '{expected_provider}', recibido '{provider}'"
            )

        display = decoded.get("name")
        if not display:
            display = email.split("@")[0] if email else str(uid)[:32]

        return VerifiedSocialIdentity(
            uid=str(uid),
            email=email,
            display_name=str(display),
            provider=provider,
        )

    def verify_google_id_token(
        self, id_token: str, *, role: str = "customer"
    ) -> VerifiedSocialIdentity:
        return self.verify_id_token(
            id_token, role=role, expected_provider="google"
        )

    def verify_apple_id_token(
        self, id_token: str, *, role: str = "customer"
    ) -> VerifiedSocialIdentity:
        return self.verify_id_token(
            id_token,
            role=role,
            expected_provider="apple",
            allow_missing_email=True,
        )


def ensure_firebase_admin_initialized() -> None:
    """Compat: inicializa app customer (o FCM_CREDENTIALS_PATH)."""
    ensure_firebase_app(FIREBASE_APP_CUSTOMER)
