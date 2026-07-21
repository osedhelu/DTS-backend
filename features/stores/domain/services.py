"""Servicios de dominio para horarios y zonas de entrega."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal

from features.stores.domain.value_objects import GeoLocation


@dataclass(frozen=True, slots=True)
class OpeningHoursSlot:
    day_of_week: int
    open_time: time | None
    close_time: time | None
    is_closed: bool


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class OpeningHoursService:
    @staticmethod
    def is_open_now(
        slots: list[OpeningHoursSlot],
        *,
        now: datetime | None = None,
    ) -> bool:
        if not slots:
            return True

        current = now or datetime.now()
        day = current.weekday()
        current_time = current.time()

        slot = next((s for s in slots if s.day_of_week == day), None)
        if slot is None or slot.is_closed:
            return False
        if slot.open_time is None or slot.close_time is None:
            return False
        if slot.open_time <= slot.close_time:
            return slot.open_time <= current_time <= slot.close_time
        return current_time >= slot.open_time or current_time <= slot.close_time


class DeliveryZoneService:
    @staticmethod
    def is_within_any_zone(
        zones: list[tuple[float, float, Decimal, bool]],
        customer: GeoLocation,
    ) -> bool:
        """zones: list of (center_lat, center_lng, radius_km, is_active)."""
        active = [z for z in zones if z[3]]
        if not active:
            return True

        for center_lat, center_lng, radius_km, _ in active:
            distance = haversine_km(
                center_lat,
                center_lng,
                customer.latitude,
                customer.longitude,
            )
            if distance <= float(radius_km):
                return True
        return False
