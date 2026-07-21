from features.accounts.application.dto import CustomerProfileResult, UpdateCustomerProfileDTO
from features.accounts.domain.exceptions import CustomerProfileNotFoundError
from features.accounts.infrastructure.models import CustomerProfile


class UpdateCustomerProfileUseCase:
    def execute(self, dto: UpdateCustomerProfileDTO) -> CustomerProfileResult:
        try:
            profile = CustomerProfile.objects.select_related("user").get(user_id=dto.customer_id)
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

        profile.save(update_fields=update_fields)

        return CustomerProfileResult(
            full_name=profile.display_full_name(),
            phone=profile.phone,
            photo_url=profile.photo_url,
            default_address=profile.default_address,
        )
