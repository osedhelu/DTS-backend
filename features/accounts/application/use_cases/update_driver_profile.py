from django.utils import timezone

from features.accounts.application.dto import DriverProfileResult, UpdateDriverProfileDTO
from features.accounts.domain.exceptions import DriverProfileNotFoundError
from features.accounts.infrastructure.models import DriverProfile


_VEHICLE_TYPES = frozenset({"moto", "carro", "bici"})


class UpdateDriverProfileUseCase:
    def execute(self, dto: UpdateDriverProfileDTO) -> DriverProfileResult:
        try:
            profile = DriverProfile.objects.get(user_id=dto.driver_id)
        except DriverProfile.DoesNotExist as exc:
            raise DriverProfileNotFoundError(
                "El conductor no tiene perfil configurado"
            ) from exc

        update_fields: list[str] = ["updated_at"]

        if dto.full_name is not None:
            profile.full_name = dto.full_name.strip()
            update_fields.append("full_name")
        if dto.phone is not None:
            profile.phone = dto.phone.strip()
            update_fields.append("phone")
        if dto.license_number is not None:
            profile.license_number = dto.license_number.strip()
            update_fields.append("license_number")
        if dto.vehicle_type is not None:
            vehicle = dto.vehicle_type.strip().lower()
            if vehicle and vehicle not in _VEHICLE_TYPES:
                from features.accounts.domain.exceptions import DomainValidationError

                raise DomainValidationError(
                    f"vehicle_type debe ser uno de: {', '.join(sorted(_VEHICLE_TYPES))}"
                )
            profile.vehicle_type = vehicle
            update_fields.append("vehicle_type")
        if dto.vehicle_plate is not None:
            profile.vehicle_plate = dto.vehicle_plate.strip().upper()
            update_fields.append("vehicle_plate")
        if dto.photo_url is not None:
            profile.photo_url = dto.photo_url.strip()
            update_fields.append("photo_url")
        if dto.bank_name is not None:
            profile.bank_name = dto.bank_name.strip()
            update_fields.append("bank_name")
        if dto.bank_account_number is not None:
            profile.bank_account_number = dto.bank_account_number.strip()
            update_fields.append("bank_account_number")
        if dto.bank_account_type is not None:
            profile.bank_account_type = dto.bank_account_type.strip()
            update_fields.append("bank_account_type")

        if dto.complete_onboarding:
            missing = []
            if not (profile.full_name or "").strip():
                missing.append("full_name")
            if not (profile.phone or "").strip():
                missing.append("phone")
            if not (profile.vehicle_type or "").strip():
                missing.append("vehicle_type")
            if not (profile.vehicle_plate or "").strip():
                missing.append("vehicle_plate")
            if missing:
                from features.accounts.domain.exceptions import DomainValidationError

                raise DomainValidationError(
                    f"Completa estos campos antes de finalizar: {', '.join(missing)}"
                )
            profile.onboarding_completed_at = timezone.now()
            update_fields.append("onboarding_completed_at")

        profile.save(update_fields=update_fields)

        return DriverProfileResult(
            full_name=profile.full_name,
            phone=profile.phone,
            license_number=profile.license_number,
            vehicle_type=profile.vehicle_type,
            vehicle_plate=profile.vehicle_plate,
            photo_url=profile.photo_url,
            onboarding_completed=profile.onboarding_completed,
            is_online=profile.is_online,
            verification_status=profile.verification_status,
            bank_name=profile.bank_name,
            bank_account_number=profile.bank_account_number,
            bank_account_type=profile.bank_account_type,
        )
