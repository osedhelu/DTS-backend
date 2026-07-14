from __future__ import annotations

from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from features.accounts.domain.entities import UserRole
from features.accounts.domain.exceptions import GoogleAccountConflictError
from features.accounts.infrastructure.firebase_token_verifier import (
    FirebaseTokenVerifier,
    VerifiedSocialIdentity,
)
from features.accounts.infrastructure.models import (
    CustomerProfile,
    CustomUser,
    DriverProfile,
)


class AppleSignInUseCase:
    def __init__(self, verifier: FirebaseTokenVerifier | None = None) -> None:
        self._verifier = verifier or FirebaseTokenVerifier()

    def execute(self, id_token: str, role: str = UserRole.CUSTOMER) -> dict[str, str]:
        if role not in (UserRole.CUSTOMER, UserRole.DRIVER):
            raise GoogleAccountConflictError(
                "Solo se admite role customer o driver para Apple Sign-In"
            )
        identity = self._verifier.verify_apple_id_token(id_token, role=role)
        user = self._get_or_create_user(identity, role=role)
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @transaction.atomic
    def _get_or_create_user(
        self, identity: VerifiedSocialIdentity, *, role: str
    ) -> CustomUser:
        user = CustomUser.objects.filter(apple_uid=identity.uid).first()
        if user is not None:
            if user.role != role:
                raise GoogleAccountConflictError(
                    "Esta cuenta Apple pertenece a otro rol; usa la app correcta"
                )
            return user

        user = CustomUser.objects.filter(email=identity.email).first()
        if user is not None:
            if user.apple_uid and user.apple_uid != identity.uid:
                raise GoogleAccountConflictError(
                    "El email ya está vinculado a otra cuenta de Apple"
                )
            if user.role != role:
                raise GoogleAccountConflictError(
                    "Esta cuenta no corresponde al rol solicitado"
                )
            user.apple_uid = identity.uid
            user.auth_provider = "apple"
            user.email_verified = True
            user.save(update_fields=["apple_uid", "auth_provider", "email_verified"])
            self._ensure_profile(user, role)
            return user

        username = self._build_username(identity.email)
        user = CustomUser(
            username=username,
            email=identity.email,
            role=role,
            email_verified=True,
            apple_uid=identity.uid,
            auth_provider="apple",
        )
        user.set_unusable_password()
        user.save()
        self._ensure_profile(user, role)
        return user

    def _ensure_profile(self, user: CustomUser, role: str) -> None:
        if role == UserRole.CUSTOMER:
            CustomerProfile.objects.get_or_create(
                user=user,
                defaults={"phone": "", "default_address": ""},
            )
        elif role == UserRole.DRIVER:
            DriverProfile.objects.get_or_create(
                user=user,
                defaults={
                    "phone": "",
                    "license_number": "",
                    "vehicle_type": "",
                },
            )

    def _build_username(self, email: str) -> str:
        base = email.split("@")[0].replace(".", "_")[:120]
        candidate = base
        suffix = 1
        while CustomUser.objects.filter(username=candidate).exists():
            candidate = f"{base}_{suffix}"
            suffix += 1
        return candidate
