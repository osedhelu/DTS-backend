from features.accounts.application.dto import CustomerAddressResult
from features.accounts.infrastructure.models import CustomerAddress


class ListCustomerAddressesUseCase:
    def execute(self, customer_id: int) -> tuple[CustomerAddressResult, ...]:
        addresses = CustomerAddress.objects.filter(user_id=customer_id)
        return tuple(
            CustomerAddressResult(
                id=address.id,
                label=address.label,
                address=address.address,
                latitude=address.latitude,
                longitude=address.longitude,
                is_default=address.is_default,
            )
            for address in addresses
        )
