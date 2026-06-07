from dataclasses import dataclass
from datetime import datetime

from features.accounts.domain.entities import UserRole
from features.stores.infrastructure.models import Store as StoreModel


@dataclass(frozen=True)
class AdminMerchantRow:
    user_id: int
    email: str
    first_name: str
    last_name: str
    email_verified: bool
    user_is_active: bool
    business_name: str
    phone: str
    store_id: int
    store_name: str
    store_vertical: str
    store_is_active: bool
    registered_at: datetime


class ListAdminMerchantsUseCase:
    def execute(
        self,
        *,
        email_verified: bool | None = None,
        user_is_active: bool | None = None,
    ) -> list[AdminMerchantRow]:
        queryset = (
            StoreModel.objects.select_related("owner", "owner__merchant_profile")
            .filter(owner__role=UserRole.MERCHANT.value)
            .order_by("-created_at")
        )

        if email_verified is not None:
            queryset = queryset.filter(owner__email_verified=email_verified)
        if user_is_active is not None:
            queryset = queryset.filter(owner__is_active=user_is_active)

        rows: list[AdminMerchantRow] = []
        for store in queryset:
            owner = store.owner
            profile = getattr(owner, "merchant_profile", None)
            rows.append(
                AdminMerchantRow(
                    user_id=owner.id,
                    email=owner.email,
                    first_name=owner.first_name,
                    last_name=owner.last_name,
                    email_verified=owner.email_verified,
                    user_is_active=owner.is_active,
                    business_name=profile.business_name if profile else "",
                    phone=profile.phone if profile else "",
                    store_id=store.id,
                    store_name=store.name,
                    store_vertical=store.vertical,
                    store_is_active=store.is_active,
                    registered_at=store.created_at,
                )
            )
        return rows
