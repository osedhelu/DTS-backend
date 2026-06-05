from features.accounts.application.dto import RegisterUserDTO
from features.accounts.domain.exceptions import DuplicateEmailError
from features.accounts.domain.repositories import UserRepository
from features.accounts.domain.value_objects import Email, Phone


class RegisterUserUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def execute(self, dto: RegisterUserDTO):
        email = Email(dto.email)
        phone = Phone(dto.phone)

        if self._user_repository.exists_by_email(email.value):
            raise DuplicateEmailError(f"El email {email.value} ya está registrado")

        return self._user_repository.register(
            {
                "username": dto.username,
                "email": email.value,
                "password": dto.password,
                "role": dto.role,
                "phone": phone.value,
                "business_name": dto.business_name,
                "tax_id": dto.tax_id or "",
                "address": dto.address or "",
                "license_number": dto.license_number or "",
                "vehicle_type": dto.vehicle_type or "",
                "default_address": dto.default_address or "",
            }
        )
