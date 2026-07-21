from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

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


@dataclass(frozen=True)
class DriverProfileResult:
    full_name: str
    phone: str
    license_number: str
    vehicle_type: str
    vehicle_plate: str
    photo_url: str
    onboarding_completed: bool
    is_online: bool
    verification_status: str = "pending"
    bank_name: str = ""
    bank_account_number: str = ""
    bank_account_type: str = ""


@dataclass(frozen=True)
class UpdateDriverProfileDTO:
    driver_id: int
    full_name: str | None = None
    phone: str | None = None
    license_number: str | None = None
    vehicle_type: str | None = None
    vehicle_plate: str | None = None
    photo_url: str | None = None
    bank_name: str | None = None
    bank_account_number: str | None = None
    bank_account_type: str | None = None
    complete_onboarding: bool = False


@dataclass(frozen=True)
class DriverEarningBreakdownItem:
    order_id: int
    completed_at: datetime
    order_total: Decimal
    earning: Decimal


@dataclass(frozen=True)
class DriverEarningsResult:
    period: str
    delivery_count: int
    total_earnings: Decimal
    currency: str
    breakdown: tuple[DriverEarningBreakdownItem, ...]


@dataclass(frozen=True)
class CustomerProfileResult:
    full_name: str
    phone: str
    photo_url: str
    default_address: str


@dataclass(frozen=True)
class UpdateCustomerProfileDTO:
    customer_id: int
    full_name: str | None = None
    phone: str | None = None
    photo_url: str | None = None
    default_address: str | None = None


@dataclass(frozen=True)
class CustomerAddressResult:
    id: int
    label: str
    address: str
    latitude: float
    longitude: float
    is_default: bool


@dataclass(frozen=True)
class CreateCustomerAddressDTO:
    customer_id: int
    label: str
    address: str
    latitude: float
    longitude: float
    is_default: bool = False


@dataclass(frozen=True)
class UpdateCustomerAddressDTO:
    customer_id: int
    address_id: int
    label: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_default: bool | None = None
