from django.db import transaction

from features.accounts.application.dto import CustomerAddressResult, UpdateCustomerAddressDTO
from features.accounts.application.sync_default_address import sync_profile_default_address
from features.accounts.domain.exceptions import CustomerAddressNotFoundError
from features.accounts.infrastructure.models import CustomerAddress


class UpdateCustomerAddressUseCase:
    @transaction.atomic
    def execute(self, dto: UpdateCustomerAddressDTO) -> CustomerAddressResult:
        try:
            address = CustomerAddress.objects.get(id=dto.address_id, user_id=dto.customer_id)
        except CustomerAddress.DoesNotExist as exc:
            raise CustomerAddressNotFoundError("Dirección no encontrada") from exc

        update_fields: list[str] = ["updated_at"]

        if dto.label is not None:
            address.label = dto.label.strip()
            update_fields.append("label")
        if dto.address is not None:
            address.address = dto.address.strip()
            update_fields.append("address")
        if dto.latitude is not None:
            address.latitude = dto.latitude
            update_fields.append("latitude")
        if dto.longitude is not None:
            address.longitude = dto.longitude
            update_fields.append("longitude")
        if dto.is_default is not None:
            if dto.is_default:
                CustomerAddress.objects.filter(
                    user_id=dto.customer_id,
                    is_default=True,
                ).exclude(id=address.id).update(is_default=False)
            address.is_default = dto.is_default
            update_fields.append("is_default")

        address.save(update_fields=update_fields)

        if address.is_default or dto.is_default is not None or dto.address is not None:
            sync_profile_default_address(dto.customer_id)

        return CustomerAddressResult(
            id=address.id,
            label=address.label,
            address=address.address,
            latitude=address.latitude,
            longitude=address.longitude,
            is_default=address.is_default,
        )
