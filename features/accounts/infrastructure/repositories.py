from typing import Any

from django.db import transaction

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import (
    CustomerProfile,
    CustomUser,
    DriverProfile,
    MerchantProfile,
)


class DjangoUserRepository:
    def exists_by_email(self, email: str) -> bool:
        return CustomUser.objects.filter(email=email).exists()

    @transaction.atomic
    def register(self, data: dict[str, Any]) -> CustomUser:
        user = CustomUser.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            role=data["role"],
        )

        role = data["role"]
        if role == UserRole.MERCHANT:
            MerchantProfile.objects.create(
                user=user,
                business_name=data["business_name"],
                tax_id=data.get("tax_id", ""),
                phone=data["phone"],
                address=data.get("address", ""),
            )
        elif role == UserRole.DRIVER:
            DriverProfile.objects.create(
                user=user,
                phone=data["phone"],
                license_number=data.get("license_number", ""),
                vehicle_type=data.get("vehicle_type", ""),
            )
        elif role == UserRole.CUSTOMER:
            CustomerProfile.objects.create(
                user=user,
                phone=data["phone"],
                default_address=data.get("default_address", ""),
            )

        return user
