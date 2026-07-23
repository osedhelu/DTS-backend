from features.accounts.application.dto import CustomerProfileResult, UpdateCustomerProfileDTO
from features.accounts.domain.exceptions import CustomerProfileNotFoundError
from features.accounts.infrastructure.models import CustomerProfile
from features.delivery.domain.constants import normalize_radius_km


def _to_result(profile: CustomerProfile) -> CustomerProfileResult:
    return CustomerProfileResult(
        full_name=profile.display_full_name(),
        email=profile.user.email,
        phone=profile.phone,
        photo_url=profile.photo_url,
        default_address=profile.default_address,
        search_center_latitude=profile.search_center_latitude,
        search_center_longitude=profile.search_center_longitude,
        search_radius_km=float(profile.search_radius_km),
    )


class UpdateCustomerProfileUseCase:
    def execute(self, dto: UpdateCustomerProfileDTO) -> CustomerProfileResult:
        try:
            profile = CustomerProfile.objects.select_related("user").get(
                user_id=dto.customer_id
            )
        except CustomerProfile.DoesNotExist as exc:
            raise CustomerProfileNotFoundError(
                "El cliente no tiene perfil configurado"
            ) from exc

        update_fields: list[str] = ["updated_at"]

        if dto.full_name is not None:
            profile.full_name = dto.full_name.strip()
            update_fields.append("full_name")
        if dto.phone is not None:
            profile.phone = dto.phone.strip()
            update_fields.append("phone")
        if dto.photo_url is not None:
            profile.photo_url = dto.photo_url.strip()
            update_fields.append("photo_url")
        if dto.default_address is not None:
            profile.default_address = dto.default_address.strip()
            update_fields.append("default_address")

        if dto.clear_search_center:
            profile.search_center_latitude = None
            profile.search_center_longitude = None
            update_fields.extend(
                ["search_center_latitude", "search_center_longitude"]
            )
        elif (
            dto.search_center_latitude is not None
            or dto.search_center_longitude is not None
        ):
            from features.accounts.domain.exceptions import DomainValidationError

            if (
                dto.search_center_latitude is None
                or dto.search_center_longitude is None
            ):
                raise DomainValidationError(
                    "Debes enviar search_center_latitude y search_center_longitude juntos"
                )
            profile.search_center_latitude = float(dto.search_center_latitude)
            profile.search_center_longitude = float(dto.search_center_longitude)
            update_fields.extend(
                ["search_center_latitude", "search_center_longitude"]
            )

        if dto.search_radius_km is not None:
            from features.accounts.domain.exceptions import DomainValidationError

            try:
                profile.search_radius_km = normalize_radius_km(dto.search_radius_km)
            except ValueError as exc:
                raise DomainValidationError(str(exc)) from exc
            update_fields.append("search_radius_km")

        profile.save(update_fields=update_fields)
        return _to_result(profile)
