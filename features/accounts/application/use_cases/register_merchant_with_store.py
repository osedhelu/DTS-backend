from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from features.accounts.application.dto import RegisterMerchantWithStoreDTO
from features.accounts.domain.entities import UserRole
from features.accounts.domain.exceptions import DuplicateEmailError
from features.accounts.domain.repositories import EmailVerificationTokenRepository
from features.accounts.domain.value_objects import Email, Phone
from features.accounts.infrastructure.models import CustomUser, MerchantProfile
from features.products.application.category_templates import seed_store_categories
from features.stores.domain.entities import StoreStatus
from features.stores.domain.repositories import StoreRepository
from features.stores.domain.value_objects import GeoLocation

TOKEN_TTL = timedelta(hours=24)


@dataclass
class RegisterMerchantWithStoreResult:
    user_id: int
    store_id: int
    verification_token: str
    email: str


class RegisterMerchantWithStoreUseCase:
    def __init__(
        self,
        user_exists_checker,
        store_repository: StoreRepository,
        token_repository: EmailVerificationTokenRepository,
    ) -> None:
        self._user_exists_checker = user_exists_checker
        self._store_repository = store_repository
        self._token_repository = token_repository

    def execute(self, dto: RegisterMerchantWithStoreDTO) -> RegisterMerchantWithStoreResult:
        email = Email(dto.email)
        phone = Phone(dto.phone)

        if self._user_exists_checker(email.value):
            raise DuplicateEmailError(f"El email {email.value} ya está registrado")

        username = self._generate_username(email.value)
        geo = GeoLocation(latitude=dto.latitude, longitude=dto.longitude)

        with transaction.atomic():
            user = CustomUser.objects.create_user(
                username=username,
                email=email.value,
                password=dto.password,
                role=UserRole.MERCHANT,
                first_name=dto.first_name.strip(),
                last_name=dto.last_name.strip(),
                email_verified=False,
                is_active=False,
            )
            MerchantProfile.objects.create(
                user=user,
                business_name=dto.store_name.strip(),
                phone=phone.value,
                address=dto.address.strip(),
            )
            store = self._store_repository.create(
                {
                    "owner_id": user.id,
                    "name": dto.store_name.strip(),
                    "latitude": geo.latitude,
                    "longitude": geo.longitude,
                    "address": dto.address.strip(),
                    "status": StoreStatus.CLOSED,
                    "vertical": dto.vertical,
                }
            )
            seed_store_categories(store.id, dto.vertical, dto.category_template)
            expires_at = timezone.now() + TOKEN_TTL
            token = self._token_repository.create(user.id, expires_at)

        return RegisterMerchantWithStoreResult(
            user_id=user.id,
            store_id=store.id,
            verification_token=token.token,
            email=email.value,
        )

    def _generate_username(self, email: str) -> str:
        base = email.split("@")[0][:120]
        candidate = base
        suffix = 1
        while CustomUser.objects.filter(username=candidate).exists():
            candidate = f"{base}{suffix}"[:150]
            suffix += 1
        return candidate
