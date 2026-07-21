from features.accounts.application.dto import CustomerProfileResult
from features.accounts.domain.exceptions import CustomerProfileNotFoundError
from features.accounts.infrastructure.models import CustomerProfile


class GetCustomerProfileUseCase:
    def execute(self, customer_id: int) -> CustomerProfileResult:
        try:
            profile = CustomerProfile.objects.select_related("user").get(user_id=customer_id)
        except CustomerProfile.DoesNotExist as exc:
            raise CustomerProfileNotFoundError(
                "El cliente no tiene perfil configurado"
            ) from exc

        return CustomerProfileResult(
            full_name=profile.display_full_name(),
            email=profile.user.email,
            phone=profile.phone,
            photo_url=profile.photo_url,
            default_address=profile.default_address,
        )
