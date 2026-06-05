from dataclasses import dataclass
from enum import StrEnum


class StoreStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class Store:
    name: str
    owner_id: int
    id: int | None = None
    status: StoreStatus = StoreStatus.CLOSED

    def open(self) -> None:
        self.status = StoreStatus.OPEN

    def close(self) -> None:
        self.status = StoreStatus.CLOSED

    def toggle_status(self) -> StoreStatus:
        if self.status == StoreStatus.OPEN:
            self.close()
        else:
            self.open()
        return self.status

    @property
    def is_open(self) -> bool:
        return self.status == StoreStatus.OPEN
