from dataclasses import dataclass

from features.accounts.domain.entities import UserRole


@dataclass(frozen=True)
class RegisterUserDTO:
    username: str
    email: str
    password: str
    role: UserRole
    phone: str
    business_name: str | None = None
    tax_id: str | None = None
    address: str | None = None
    license_number: str | None = None
    vehicle_type: str | None = None
    default_address: str | None = None
