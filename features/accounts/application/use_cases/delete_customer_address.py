from django.db import transaction

from features.accounts.application.sync_default_address import sync_profile_default_address
from features.accounts.domain.exceptions import CustomerAddressNotFoundError
from features.accounts.infrastructure.models import CustomerAddress


class DeleteCustomerAddressUseCase:
    @transaction.atomic
    def execute(self, customer_id: int, address_id: int) -> None:
        try:
            address = CustomerAddress.objects.get(id=address_id, user_id=customer_id)
        except CustomerAddress.DoesNotExist as exc:
            raise CustomerAddressNotFoundError("Dirección no encontrada") from exc

        was_default = address.is_default
        address.delete()

        if was_default:
            sync_profile_default_address(customer_id)
        else:
            # Still refresh if profile was out of sync
            remaining = CustomerAddress.objects.filter(user_id=customer_id).exists()
            if not remaining:
                sync_profile_default_address(customer_id)
