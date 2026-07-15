from features.accounts.application.dto import DriverProfileResult
from features.accounts.domain.exceptions import DriverProfileNotFoundError
from features.accounts.infrastructure.models import DriverProfile


class GetDriverProfileUseCase:
    def execute(self, driver_id: int) -> DriverProfileResult:
        try:
            profile = DriverProfile.objects.get(user_id=driver_id)
        except DriverProfile.DoesNotExist as exc:
            raise DriverProfileNotFoundError(
                "El conductor no tiene perfil configurado"
            ) from exc

        return DriverProfileResult(
            full_name=profile.full_name,
            phone=profile.phone,
            license_number=profile.license_number,
            vehicle_type=profile.vehicle_type,
            vehicle_plate=profile.vehicle_plate,
            photo_url=profile.photo_url,
            onboarding_completed=profile.onboarding_completed,
            is_online=profile.is_online,
        )
