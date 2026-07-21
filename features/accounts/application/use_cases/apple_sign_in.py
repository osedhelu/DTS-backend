from __future__ import annotations

from django.db import transaction

from features.accounts.domain.entities import UserRole
from features.accounts.domain.exceptions import GoogleAccountConflictError
from features.accounts.infrastructure.firebase_token_verifier import (
    FirebaseTokenVerifier,
    VerifiedSocialIdentity,
)
from features.accounts.infrastructure.jwt_tokens import issue_tokens_for_user
from features.accounts.infrastructure.models import (
    CustomerProfile,
    CustomUser,
    DriverProfile,
)


class AppleSignInUseCase:
    def __init__(self, verifier: FirebaseTokenVerifier | None = None) -> None:
        self._verifier = verifier or FirebaseTokenVerifier()

    def execute(
        self,
        id_token: str,
        role: str = UserRole.CUSTOMER,
        *,
        email: str | None = None,
        full_name: str | None = None,
    ) -> dict[str, str]:
        if role not in (UserRole.CUSTOMER, UserRole.DRIVER):
            raise GoogleAccountConflictError(
                "Solo se admite role customer o driver para Apple Sign-In"
            )
        identity = self._verifier.verify_apple_id_token(id_token, role=role)
        resolved = self._resolve_identity(
            identity, email=email, full_name=full_name
        )
        user = self._get_or_create_user(resolved, role=role)
        return issue_tokens_for_user(user)

    def _resolve_identity(
        self,
        identity: VerifiedSocialIdentity,
        *,
        email: str | None,
        full_name: str | None,
    ) -> VerifiedSocialIdentity:
        resolved_email = identity.email or (
            email.lower().strip() if email else None
        )
        if resolved_email is None:
            # Usuario existente se resuelve por apple_uid; placeholder solo para altas.
            existing = CustomUser.objects.filter(apple_uid=identity.uid).first()
            if existing is not None:
                resolved_email = existing.email
            else:
                resolved_email = f"{identity.uid}@privaterelay.appleid.local"

        display = full_name.strip() if full_name else identity.display_name
        return VerifiedSocialIdentity(
            uid=identity.uid,
            email=resolved_email,
            display_name=display or resolved_email.split("@")[0],
            photo_url=identity.photo_url,
            provider="apple",
        )

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

        assert identity.email is not None
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
            self._ensure_profile(user, role, identity)
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
        self._ensure_profile(user, role, identity)
        return user

    def _ensure_profile(
        self,
        user: CustomUser,
        role: str,
        identity: VerifiedSocialIdentity,
    ) -> None:
        if role == UserRole.CUSTOMER:
            profile, _ = CustomerProfile.objects.get_or_create(
                user=user,
                defaults={"phone": "", "default_address": ""},
            )
            update_fields: list[str] = []
            if not profile.full_name.strip() and identity.display_name.strip():
                profile.full_name = identity.display_name.strip()
                update_fields.append("full_name")
            if not profile.photo_url.strip() and identity.photo_url.strip():
                profile.photo_url = identity.photo_url.strip()
                update_fields.append("photo_url")
            if update_fields:
                update_fields.append("updated_at")
                profile.save(update_fields=update_fields)
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
