from dataclasses import dataclass

from features.accounts.domain.entities import UserRole
from features.stores.domain.entities import StoreVertical


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


@dataclass(frozen=True)
class RegisterMerchantWithStoreDTO:
    email: str
    password: str
    first_name: str
    last_name: str
    store_name: str
    vertical: StoreVertical
    category_template: str
    phone: str
    address: str = ""
    latitude: float = 0.0
    longitude: float = 0.0


@dataclass(frozen=True)
class UpdateDriverAvailabilityDTO:
    driver_id: int
    is_online: bool
    latitude: float | None = None
    longitude: float | None = None


@dataclass(frozen=True)
class DriverAvailabilityResult:
    is_online: bool
    latitude: float | None
    longitude: float | None
