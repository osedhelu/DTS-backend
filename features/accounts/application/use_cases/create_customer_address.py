from django.db import transaction

from features.accounts.application.dto import CreateCustomerAddressDTO, CustomerAddressResult
from features.accounts.application.sync_default_address import sync_profile_default_address
from features.accounts.infrastructure.models import CustomerAddress


class CreateCustomerAddressUseCase:
    @transaction.atomic
    def execute(self, dto: CreateCustomerAddressDTO) -> CustomerAddressResult:
        if dto.is_default:
            CustomerAddress.objects.filter(user_id=dto.customer_id, is_default=True).update(
                is_default=False
            )

        address = CustomerAddress.objects.create(
            user_id=dto.customer_id,
            label=dto.label.strip(),
            address=dto.address.strip(),
            latitude=dto.latitude,
            longitude=dto.longitude,
            is_default=dto.is_default,
        )

        if address.is_default:
            sync_profile_default_address(dto.customer_id)

        return CustomerAddressResult(
            id=address.id,
            label=address.label,
            address=address.address,
            latitude=address.latitude,
            longitude=address.longitude,
            is_default=address.is_default,
        )
