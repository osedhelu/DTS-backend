from dataclasses import dataclass

from features.stores.domain.entities import StoreStatus


@dataclass(frozen=True)
class CreateStoreDTO:
    owner_id: int
    name: str
    latitude: float
    longitude: float
    address: str = ""
    status: StoreStatus = StoreStatus.CLOSED


@dataclass(frozen=True)
class UpdateStoreStatusDTO:
    store_id: int
    owner_id: int
    status: StoreStatus


@dataclass(frozen=True)
class UpdateStoreProfileDTO:
    store_id: int
    owner_id: int
    name: str | None = None
    description: str | None = None
    phone: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: StoreStatus | None = None
    logo_file: object | None = None
