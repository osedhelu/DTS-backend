from features.accounts.application.dto import (
    DriverAvailabilityResult,
    UpdateDriverAvailabilityDTO,
)
from features.accounts.domain.exceptions import DriverProfileNotFoundError
from features.accounts.infrastructure.models import DriverProfile
from features.stores.domain.value_objects import GeoLocation


class UpdateDriverAvailabilityUseCase:
    def execute(self, dto: UpdateDriverAvailabilityDTO) -> DriverAvailabilityResult:
        try:
            profile = DriverProfile.objects.get(user_id=dto.driver_id)
        except DriverProfile.DoesNotExist as exc:
            raise DriverProfileNotFoundError(
                "El conductor no tiene perfil configurado"
            ) from exc

        profile.is_online = dto.is_online

        if dto.latitude is not None and dto.longitude is not None:
            profile.set_last_location(
                GeoLocation(latitude=dto.latitude, longitude=dto.longitude)
            )

        profile.save(
            update_fields=[
                "is_online",
                "last_latitude",
                "last_longitude",
                "updated_at",
            ]
        )

        return DriverAvailabilityResult(
            is_online=profile.is_online,
            latitude=profile.last_latitude,
            longitude=profile.last_longitude,
        )
