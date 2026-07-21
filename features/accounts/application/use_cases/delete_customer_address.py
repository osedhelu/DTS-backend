from features.accounts.domain.exceptions import CustomerAddressNotFoundError
from features.accounts.infrastructure.models import CustomerAddress


class DeleteCustomerAddressUseCase:
    def execute(self, customer_id: int, address_id: int) -> None:
        deleted, _ = CustomerAddress.objects.filter(
            id=address_id,
            user_id=customer_id,
        ).delete()
        if deleted == 0:
            raise CustomerAddressNotFoundError("Dirección no encontrada")
