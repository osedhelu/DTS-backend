from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RecordLocationDTO:
    order_id: int
    driver_id: int
    latitude: float
    longitude: float
    recorded_at: datetime
